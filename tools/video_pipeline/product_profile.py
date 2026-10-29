"""
product_profile.py
──────────────────
Extracts a factually grounded ProductProfile from crawled page data and assets.
Uses call_director() with ProductProfile Pydantic schema, followed by deterministic
code-level post-validation:
- Strips hallucinated asset filenames (must exist on disk)
- Drops proof points not grounded in crawl text
- Strictly enforces missing_data tracking (price, rating, logo)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from tools.video_pipeline.director import call_director, DirectorError
from tools.video_pipeline.schemas import ProductProfile, ProofPoint, ToneEnum

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _safe_str(text: Any) -> str:
    """Returns a string safe for console output across all Windows encodings."""
    try:
        return str(text).encode("ascii", errors="replace").decode("ascii")
    except Exception:
        return ""


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
PROFILE_PROMPT_PATH = PROMPTS_DIR / "profile.md"


def load_system_prompt() -> str:
    """Loads the system prompt markdown for product profile extraction."""
    if PROFILE_PROMPT_PATH.exists():
        return PROFILE_PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are an expert Creative Director. Extract a strict, factually grounded "
        "ProductProfile JSON object from the provided crawl data. Never invent facts."
    )


def build_crawl_digest(
    brand_data: Dict[str, Any],
    ui_desc: Optional[Dict[str, Any]] = None,
    discovered_assets: Optional[List[str]] = None,
    raw_text: str = ""
) -> Tuple[str, Dict[str, bool]]:
    """
    Compiles raw crawl data into a clean, token-bounded prompt string.
    Returns the formatted prompt and a presence-map of ground-truth features.
    """
    name = brand_data.get("name", "Product")
    domain = brand_data.get("domain", "")
    tagline = brand_data.get("tagline", "")
    description = brand_data.get("description", "")
    products = brand_data.get("products", [])
    
    # Check what was genuinely extracted from the crawl
    has_price = False
    price_info = ui_desc.get("price_info") if ui_desc else None
    if price_info and (price_info.get("current") or price_info.get("original")):
        has_price = True

    has_rating = False
    rating_info = ui_desc.get("rating") if ui_desc else None
    if rating_info and (rating_info.get("value") is not None or rating_info.get("count_text")):
        has_rating = True

    has_logo = False
    logo_data = brand_data.get("logo")
    if logo_data and isinstance(logo_data, dict) and logo_data.get("src"):
        has_logo = True

    badges = ui_desc.get("trust_badges", []) if ui_desc else []
    distinguishers = ui_desc.get("brand_distinguishers", []) if ui_desc else []
    nav_links = ui_desc.get("header", {}).get("navLinks", []) if ui_desc else []

    ground_truth_map = {
        "price": has_price,
        "rating": has_rating,
        "logo": has_logo,
        "product_image": bool(discovered_assets and len(discovered_assets) > 0)
    }

    # Trim raw crawl text to avoid blowing token limits (~4000 chars)
    trimmed_text = (raw_text or description or "").strip()[:4000]

    digest = f"""PRODUCT CRAWL DATA:
- Name: {name}
- Domain: {domain}
- Tagline / Hero Heading: {tagline}
- Description: {description}
- Products / Features Listed: {', '.join(products) if products else 'None explicit'}
- Navigation Categories: {', '.join(nav_links) if nav_links else 'None'}
- Trust Badges Extracted: {', '.join(badges) if badges else 'None'}
- Brand Distinguishers: {', '.join(distinguishers) if distinguishers else 'None'}

PRICING & REPUTATION DATA EXTRACTED:
- Real Price Data: {json.dumps(price_info) if has_price else 'NONE EXTRACTED FROM PAGE'}
- Real Rating Data: {json.dumps(rating_info) if has_rating else 'NONE EXTRACTED FROM PAGE'}

DISCOVERED VISUAL ASSETS ON DISK:
{json.dumps(discovered_assets or [])}

PAGE BODY TEXT EXCERPT (Ground Truth Reference):
\"\"\"
{trimmed_text}
\"\"\"
"""
    return digest, ground_truth_map


def post_validate_profile(
    profile: ProductProfile,
    disk_assets: List[str],
    raw_crawl_corpus: str,
    ground_truth: Dict[str, bool]
) -> ProductProfile:
    """
    Deterministic post-validation:
    1. Strips any asset filename that does not exist in disk_assets.
    2. Drops proof points whose text cannot be verified against crawl corpus.
    3. Guarantees missing_data accurately lists unextracted elements.
    4. Ensures no price/rating appears in proof points if not in ground truth.
    """
    # 1. Filter visual assets to only genuinely existing files
    valid_assets_set = set(disk_assets)
    filtered_assets = [a for a in profile.visual_assets_available if a in valid_assets_set]
    if len(filtered_assets) != len(profile.visual_assets_available):
        hallucinated = set(profile.visual_assets_available) - valid_assets_set
        print(f"[post-validation] [WARN] Stripped hallucinated assets: {hallucinated}")
    profile.visual_assets_available = filtered_assets

    # 2. Filter proof points
    corpus_lower = raw_crawl_corpus.lower()
    verified_proof_points: List[ProofPoint] = []

    for pp in profile.proof_points:
        # Check if price was claimed when no price was extracted
        if not ground_truth.get("price") and any(ch in pp.text for ch in ["₹", "$", "€", "£", "% off", "percent off"]):
            print(f"[post-validation] [WARN] Dropped unextracted price claim from proof points: '{_safe_str(pp.text)}'")
            continue

        # Check if rating was claimed when no rating was extracted
        if not ground_truth.get("rating") and any(k in pp.text.lower() for k in ["star", "rating", "rated", "/5"]):
            print(f"[post-validation] [WARN] Dropped unextracted rating claim from proof points: '{_safe_str(pp.text)}'")
            continue

        # Check text grounding: at least significant keywords or words must exist in corpus
        words = [w for w in pp.text.lower().split() if len(w) > 3]
        if words:
            matching_words = sum(1 for w in words if w in corpus_lower)
            # Require at least 40% keyword presence or full phrase match
            if matching_words / len(words) < 0.35 and pp.text.lower() not in corpus_lower:
                print(f"[post-validation] [WARN] Dropped ungrounded proof point: '{_safe_str(pp.text)}'")
                continue

        verified_proof_points.append(pp)

    profile.proof_points = verified_proof_points

    # 3. Synchronize missing_data with ground truth
    missing_set = set(profile.missing_data)
    for key, is_present in ground_truth.items():
        if not is_present:
            missing_set.add(key)
        else:
            # If genuinely present, remove from missing_set
            missing_set.discard(key)
    profile.missing_data = sorted(list(missing_set))

    return profile


def extract_product_profile(
    brand_data: Dict[str, Any],
    ui_desc: Optional[Dict[str, Any]] = None,
    assets_dir: Optional[Path] = None,
    raw_text: str = "",
    run_id: Optional[str] = None
) -> ProductProfile:
    """
    Extracts, validates, and post-validates a ProductProfile for a product.
    """
    # 1. Discover actual assets on disk
    disk_assets: List[str] = []
    if assets_dir and assets_dir.exists():
        for f in assets_dir.iterdir():
            if f.is_file() and f.suffix.lower() in [".png", ".jpg", ".jpeg", ".svg", ".webp"]:
                disk_assets.append(f.name)

    # 2. Build Crawl Digest
    user_prompt, ground_truth = build_crawl_digest(
        brand_data=brand_data,
        ui_desc=ui_desc,
        discovered_assets=disk_assets,
        raw_text=raw_text or brand_data.get("description", "")
    )

    system_prompt = load_system_prompt()

    # 3. Call Director Gateway
    raw_profile = call_director(
        system=system_prompt,
        user=user_prompt,
        schema=ProductProfile,
        retries=2,
        temperature=0.7,
        step_name="product_profile",
        run_id=run_id
    )

    # 4. Deterministic Post-Validation
    corpus = f"{brand_data.get('name', '')} {brand_data.get('tagline', '')} {brand_data.get('description', '')} {raw_text}"
    if ui_desc:
        corpus += f" {' '.join(ui_desc.get('trust_badges', []))} {' '.join(ui_desc.get('brand_distinguishers', []))}"

    validated_profile = post_validate_profile(
        profile=raw_profile,
        disk_assets=disk_assets,
        raw_crawl_corpus=corpus,
        ground_truth=ground_truth
    )

    return validated_profile


# ──────────────────────────────────────────────────────────────────────────────
# CLI Entrypoint
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract ProductProfile via Director Gateway")
    parser.add_argument("--job-dir", required=True, help="Path to job directory (contains brand.json, assets/)")
    parser.add_argument("--output-json", help="Path to write product_profile.json (defaults to <job-dir>/product_profile.json)")
    parser.add_argument("--run-id", default=None, help="Optional run id for director logging")
    args = parser.parse_args()

    job_path = Path(args.job_dir).resolve()
    brand_file = job_path / "brand.json"
    ui_desc_file = job_path / "ui_description.json"
    assets_path = job_path / "assets"

    if not brand_file.exists():
        print(f"[product_profile] ❌ brand.json not found in {job_path}")
        sys.exit(1)

    with open(brand_file, "r", encoding="utf-8") as f:
        brand_data = json.load(f)

    ui_desc = None
    if ui_desc_file.exists():
        with open(ui_desc_file, "r", encoding="utf-8") as f:
            ui_desc = json.load(f)

    print(f"[product_profile] Analyzing brand: {brand_data.get('name')} ({brand_data.get('domain')})...")
    profile = extract_product_profile(
        brand_data=brand_data,
        ui_desc=ui_desc,
        assets_dir=assets_path,
        run_id=args.run_id or job_path.name
    )

    out_path = Path(args.output_json) if args.output_json else job_path / "product_profile.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(), f, indent=2)

    print(f"[product_profile] ✅ product_profile.json written to {out_path}")
    print(f"  • Category: {profile.category}")
    print(f"  • Tone: {profile.tone.value}")
    print(f"  • Differentiator: {profile.core_differentiator}")
    print(f"  • Proof Points ({len(profile.proof_points)}): {[p.text for p in profile.proof_points]}")
    print(f"  • Missing Data: {profile.missing_data}")
    print(f"  • Verified Assets: {profile.visual_assets_available}")


if __name__ == "__main__":
    main()
