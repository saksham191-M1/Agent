import os
import sys

_curr_dir = os.path.dirname(os.path.abspath(__file__))
if _curr_dir not in sys.path:
    sys.path.insert(0, _curr_dir)

_root_dir = os.path.abspath(os.path.join(_curr_dir, "../.."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

import json
import re
import requests
from dotenv import load_dotenv
from colorama import Fore, init
from ml_prompt_matcher import OpusPromptMLMatcher

from tools.video_pipeline.schemas import (
    ProductProfile,
    ToneEnum,
    ProofPoint,
    NarrativeArc,
    StoryboardDirectorSpec,
    SceneDirectorSpec
)
from tools.video_pipeline.narratives import select_narrative, load_narratives
from tools.video_pipeline.storyboard_director import generate_storyboard, sanitize_storyboard

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))
init(autoreset=True)


REFERENCE_MAX_CHARS = 3500
LOW_MATCH_SCORE = 0.25
REFERENCE_BLOCKS = ("direction", "gotchas", "structure")

DEFAULT_MOTION_CONSTRAINTS = """
    STRICT MOTION RULES (v1.0):
    - Camera: Never fully stops; continuous subtle push scale (1.03 to 1.07).
    - Text Entry: Mask line rise with per-letter stagger (no terminal periods/punctuation on headlines).
    - Transitions: Use 'carousel_glide' or 'cross_zoom'. NEVER use hard cuts, white flashes, or crossfades between scenes.
    - Objects: Slow sway idle (1-3 degrees, 4-7s period). Never appear instantly.
    - Counters: Count up using ease_out_cubic over 1.5-3.0s.
    - Frame Rate: 60 fps pure function of time render(t).
    """


def _prompt_blocks(prompt):
    """Split an Opus prompt into its tagged blocks, e.g. <direction>...</direction>."""
    return {name.lower(): body.strip() for name, body in re.findall(r"<(\w+)>(.*?)</\1>", prompt or "", re.S)}


def build_reference_inspiration(best_match):
    """
    Give the model the reference's look, motion and structure, not just its first
    350 characters. The <inputs>/<start> blocks are skipped on purpose: they hold the
    reference product's own defaults, which must not leak into this product's ad.
    """
    if not best_match:
        return ""
    prompt = best_match.get("prompt") or ""
    blocks = _prompt_blocks(prompt)
    parts, used = [], 0
    for name in REFERENCE_BLOCKS:
        body = blocks.get(name)
        room = REFERENCE_MAX_CHARS - used
        if not body or room < 200:
            continue
        body = body[:room]
        parts.append(f"[{name.upper()}]\n{body}")
        used += len(body)
    if not parts:
        parts.append(prompt[:1500])
    excerpt = "\n\n".join(parts)
    return f"""
    VIRAL OPUS 5.5 INSPIRATION (Inherited from @{best_match['author']}, Category: {best_match['category'].upper()}):
    Tech tags: {', '.join(best_match['tech_tags'])}
    Reference prompt excerpt (use for motion pacing, visual language and structure only):
    {excerpt}

    Emulate this motion pacing, visual metaphor, and kinetic elegance in the scene breakdown!
    Use the reference for HOW the ad moves and looks. Do NOT reuse its product name, copy lines, characters or story: the ad is about the product above.
    """


def build_motion_constraints(rules):
    """Build the motion-rule text from motion_rules.json so the file is the single source."""
    if not rules:
        return DEFAULT_MOTION_CONSTRAINTS
    try:
        push = rules["camera"]["push_scale_per_scene"]
        te = rules["text_entry"]
        sw = rules["transitions"]["scene_swap"]
        ob = rules["objects"]
        ct = rules["counters"]
        banned = ", ".join(b.replace("_", " ") for b in rules["banned"])
        return f"""
    STRICT MOTION RULES (v{rules.get('version', '1.0')}):
    - Camera: Never fully stops; continuous subtle push scale ({push[0]} to {push[1]}).
    - Text Entry: {te['method'].replace('_', ' ')} with per-letter stagger (no terminal periods/punctuation on headlines).
    - Transitions: Use '{sw['type']}' or 'cross_zoom'. NEVER use hard cuts, white flashes, or crossfades between scenes.
    - Objects: Slow sway idle ({ob['sway_degrees'][0]}-{ob['sway_degrees'][1]} degrees, {ob['sway_period_seconds'][0]}-{ob['sway_period_seconds'][1]}s period). Never appear instantly.
    - Counters: Count up using {ct['easing']} over {ct['duration_seconds'][0]}-{ct['duration_seconds'][1]}s.
    - Frame Rate: {rules['render']['fps']} fps pure function of time render(t).
    - Banned: {banned}.
    """
    except (KeyError, IndexError, TypeError):
        return DEFAULT_MOTION_CONSTRAINTS


def extract_opus_aesthetic(prompt, author=""):
    """
    Autonomously extracts the color palette, light/dark theme intent,
    and motion rules directly from the matched Opus prompt.
    """
    if not prompt:
        return {
            "is_light_theme": False,
            "background": "#0B1020",
            "background2": "#151B33",
            "surface": "#1E293B",
            "surfaceText": "#F8FAFC",
            "text": "#F8FAFC",
            "muted": "#94A3B8",
            "accent": "#6C5CE7",
            "accentLight": "#B9B0FF",
            "secondary": "#FF7DC7",
            "motion_rules": ["smooth_transition"],
            "suggested_bpm": 120
        }

    p_lower = prompt.lower()
    light_signals = ["cream", "off-white", "paper", "light canvas", "light warm-gray", "white background", "cream disc"]
    is_light = any(sig in p_lower for sig in light_signals)

    labeled_hex = re.findall(r'([a-zA-Z\-_\s]{2,15})?\s*(#[0-9a-fA-F]{6})', prompt)
    hex_map = {}
    for lbl, hx in labeled_hex:
        clean_lbl = lbl.strip().lower()
        hex_map[clean_lbl] = hx.upper()

    raw_hexes = [hx.upper() for _, hx in labeled_hex]

    if is_light:
        bg = hex_map.get("cream") or hex_map.get("paper") or hex_map.get("canvas") or "#F6E4C6"
        txt = hex_map.get("ink") or hex_map.get("dark") or hex_map.get("black") or "#0E0F1F"
        surf = "#FFFFFF"
        surf_txt = txt
        accent = hex_map.get("cobalt") or hex_map.get("blue") or (raw_hexes[0] if len(raw_hexes) > 0 and raw_hexes[0] != bg else "#2B3BFF")
        accent_light = hex_map.get("pink") or hex_map.get("coral") or (raw_hexes[1] if len(raw_hexes) > 1 and raw_hexes[1] not in (bg, accent) else "#FF7DC7")
        secondary = hex_map.get("tangerine") or hex_map.get("orange") or (raw_hexes[2] if len(raw_hexes) > 2 and raw_hexes[2] not in (bg, accent, accent_light) else "#FF5A1F")
        bg2 = "#EDE0CA"
        muted = "#6B7280"
    else:
        bg = hex_map.get("ink") or hex_map.get("dark") or hex_map.get("black") or (raw_hexes[0] if raw_hexes else "#0B1020")
        txt = hex_map.get("white") or hex_map.get("cream") or "#F8FAFC"
        surf = "#1E293B"
        surf_txt = "#F8FAFC"
        accent = hex_map.get("accent") or (raw_hexes[1] if len(raw_hexes) > 1 else "#6C5CE7")
        accent_light = (raw_hexes[2] if len(raw_hexes) > 2 else "#B9B0FF")
        secondary = (raw_hexes[3] if len(raw_hexes) > 3 else "#38BDF8")
        bg2 = "#151B33"
        muted = "#94A3B8"

    bpm_match = re.search(r'(\d{2,3}(?:\.\d+)?)\s*BPM', prompt, re.I)
    suggested_bpm = float(bpm_match.group(1)) if bpm_match else 120

    motion_rules = []
    if "camera never stops" in p_lower or "push" in p_lower:
        motion_rules.append("continuous_camera_push")
    if "film grain" in p_lower:
        motion_rules.append("film_grain")
    if "die-cut" in p_lower or "sticker" in p_lower:
        motion_rules.append("die_cut_accents")

    return {
        "is_light_theme": is_light,
        "background": bg,
        "background2": bg2,
        "surface": surf,
        "surfaceText": surf_txt,
        "text": txt,
        "muted": muted,
        "accent": accent,
        "accentLight": accent_light,
        "secondary": secondary,
        "suggested_bpm": round(suggested_bpm),
        "motion_rules": motion_rules
    }

def load_global_motion_rules():
    rule_path = os.path.join(_curr_dir, "motion_rules.json")
    if os.path.exists(rule_path):
        try:
            with open(rule_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def infer_tone_from_category(category: str, description: str = "") -> ToneEnum:
    c = f"{category} {description}".lower()
    if any(k in c for k in ["luxury", "exclusive", "fashion", "premium", "watch", "jewelry"]):
        return ToneEnum.premium
    if any(k in c for k in ["code", "dev", "database", "api", "infra", "cloud", "sdk"]):
        return ToneEnum.technical
    if any(k in c for k in ["sale", "deal", "discount", "urgency", "now", "black friday"]):
        return ToneEnum.urgent
    if any(k in c for k in ["social", "creator", "game", "snack", "food", "fun"]):
        return ToneEnum.playful
    if any(k in c for k in ["minimal", "clean", "zen", "simple", "calm"]):
        return ToneEnum.minimal
    if any(k in c for k in ["health", "care", "family", "community", "wellness"]):
        return ToneEnum.warm
    return ToneEnum.bold


def build_arc_fallback_storyboard(product_name: str, arc: NarrativeArc, profile: ProductProfile, aesthetic: dict) -> dict:
    """Builds a dynamic fallback storyboard adhering to the chosen arc blueprints without fake data."""
    scenes = []
    for idx, bp in enumerate(arc.scene_blueprints, start=1):
        layout = bp.allowed_layouts[0] if bp.allowed_layouts else "hero-type"
        motion = bp.allowed_motion[0] if bp.allowed_motion else "smooth"
        requires_ui = layout in ["phone", "browser", "split"]
        headline = product_name.upper() if idx == 1 else bp.role.upper().replace("_", " ")
        headline = re.sub(r"[\.\:\;\!\?\,]+$", "", headline).strip()

        scenes.append({
            "scene_id": idx,
            "duration_seconds": bp.target_duration,
            "layout": layout,
            "motion_profile": motion,
            "voiceover": f"{bp.vo_instruction} for {product_name}.",
            "kinetic_text": headline,
            "visual_fx": "carousel_glide",
            "transition_out": "carousel_glide",
            "requires_ui_image": requires_ui,
            "veo_prompt": f"Cinematic visual for {bp.role} scene of {product_name}"
        })
    total_sec = round(sum(s["duration_seconds"] for s in scenes), 2)
    return {
        "product_name": product_name,
        "selected_template": arc.name,
        "narrative_type": arc.id,
        "matched_opus_category": "MOTION",
        "aesthetic": aesthetic,
        "scene_count": len(scenes),
        "total_seconds": total_sec,
        "music_mood": "ambient_electronic",
        "voice_style": "confident_conversational",
        "scenes": scenes
    }


def generate_multi_scene_blueprint(product_name, description="", return_match=False, output_json_path=None):
    global_rules = load_global_motion_rules()

    # ML Prompt Matching against curated Opus viral references
    matcher = OpusPromptMLMatcher()
    match_result = matcher.find_best_prompts(product_name, description, top_k=1)
    best_match = match_result["top_matches"][0] if match_result["top_matches"] else None
    
    category = best_match['category'] if best_match else "technology"
    if best_match:
        print(f"{Fore.CYAN}🎯 ML Matched Category: {best_match['category'].upper()} (Score: {best_match['score']:.4f}){Fore.RESET}")
        print(f"{Fore.CYAN}💡 Viral Inspiration: @{best_match['author']} ({', '.join(best_match['tech_tags'])}){Fore.RESET}")
        print(f"{Fore.CYAN}🔗 Reference: {best_match['skillry_url'] or best_match['post_url']}{Fore.RESET}")
        if best_match['score'] < LOW_MATCH_SCORE:
            print(f"{Fore.YELLOW}⚠️ Low match score ({best_match['score']:.2f}): review the storyboard.{Fore.RESET}")

    aesthetic = extract_opus_aesthetic(best_match['prompt'] if best_match else '', author=best_match.get('author', '') if best_match else '')

    # Try loading crawled brand.json if available from job dir
    brand_data = None
    if output_json_path:
        candidate_brand = os.path.join(os.path.dirname(os.path.abspath(output_json_path)), "brand.json")
        if os.path.exists(candidate_brand):
            try:
                with open(candidate_brand, "r", encoding="utf-8") as f:
                    brand_data = json.load(f)
                print(f"{Fore.CYAN}📁 Loaded crawled brand context from {candidate_brand}{Fore.RESET}")
            except Exception:
                pass

    # Build ProductProfile
    proof_points = []
    missing_data = []
    visual_assets = []

    if brand_data:
        for claim in brand_data.get("claims", []):
            if claim.get("value"):
                proof_points.append(ProofPoint(text=claim["value"], source=claim.get("sourceUrl", "brand.json")))
        if not brand_data.get("price_info"):
            missing_data.append("price")
        if not brand_data.get("rating"):
            missing_data.append("rating")
        for img in brand_data.get("imagery", []):
            if isinstance(img, dict) and img.get("src"):
                visual_assets.append(os.path.basename(img["src"]))
            elif isinstance(img, str):
                visual_assets.append(os.path.basename(img))
    else:
        missing_data = ["price", "rating", "discount"]

    visual_rules = aesthetic.get("motion_rules", []) if aesthetic else []
    visual_hint = visual_rules[0] if visual_rules else "clean modern UI"

    tone = infer_tone_from_category(category, description)
    profile = ProductProfile(
        name=product_name,
        what_it_is=description or f"{product_name} modern solution",
        audience="Users and decision makers seeking quality solutions",
        core_differentiator=description.split(".")[0] if description else f"Fast modern {product_name}",
        tone=tone,
        category=category,
        visual_style_hint=visual_hint,
        proof_points=proof_points,
        visual_assets_available=visual_assets,
        missing_data=missing_data,
        language="en"
    )

    # Intelligent Narrative Arc Selection
    selected_arc = select_narrative(profile)
    print(f"{Fore.MAGENTA}🎭 Selected Narrative Arc: {selected_arc.name} ({selected_arc.id}){Fore.RESET}")

    response_text = None

    # Execute Dynamic Storyboard Generation & Critique Gate via Director AI Gateway
    try:
        storyboard_spec = generate_storyboard(profile, selected_arc, run_id=f"run_{product_name.lower()[:8]}")
        data = storyboard_spec.model_dump()
        data["aesthetic"] = aesthetic
        data["matched_opus_category"] = category.upper()
        data["selected_template"] = selected_arc.name
        response_text = json.dumps(data)
        print(f"{Fore.GREEN}✅ Director AI Gateway successfully generated and validated storyboard!{Fore.RESET}")
    except Exception as err:
        print(f"{Fore.YELLOW}⚠️ Director AI Gateway error: {err}. Using arc-aligned dynamic fallback.{Fore.RESET}")
        fallback_dict = build_arc_fallback_storyboard(product_name, selected_arc, profile, aesthetic)
        response_text = json.dumps(fallback_dict)
        
    if return_match:
        return response_text, best_match
    return response_text

if __name__ == "__main__":
    # Parse args: brain_opus.py <product_name> [desc] [--output-json <path>]
    positional = []
    output_json_path = None
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--output-json" and i + 1 < len(sys.argv):
            output_json_path = sys.argv[i + 1]
            i += 2
        else:
            positional.append(sys.argv[i])
            i += 1

    if len(positional) == 0:
        print(f"{Fore.RED}Error: Product name argument is required.{Fore.RESET}")
        sys.exit(1)
    app = positional[0]
    desc = positional[1] if len(positional) > 1 else ""

    print(f"{Fore.CYAN}=== OPUS DIRECTOR AI: AUTONOMOUS STORYBOARD FOR '{app.upper()}' ==={Fore.RESET}\n")
    
    try:
        raw_result, best_match = generate_multi_scene_blueprint(app, desc, return_match=True, output_json_path=output_json_path)
        cleaned_json = raw_result.replace('```json', '').replace('```', '').strip()
        data = json.loads(cleaned_json)
        
        extracted_aesthetic = extract_opus_aesthetic(best_match['prompt'] if best_match else '', author=best_match.get('author', '') if best_match else '')
        if 'aesthetic' not in data or not data['aesthetic']:
            data['aesthetic'] = extracted_aesthetic

        if best_match:
            data['ml_match'] = {
                'category': best_match.get('category', '').upper(),
                'score': float(best_match.get('score', 0)),
                'author': best_match.get('author', ''),
                'tech_tags': best_match.get('tech_tags', []),
                'prompt_snippet': best_match.get('prompt', '')[:350],
                'reference_url': best_match.get('skillry_url') or best_match.get('post_url') or '',
                'aesthetic': data['aesthetic']
            }
        
        print(f"{Fore.MAGENTA}Chosen Template: {data['selected_template']}{Fore.RESET}")
        print(f"{Fore.CYAN}🎨 Extracted Opus Palette: Background: {data['aesthetic']['background']} | Text: {data['aesthetic']['text']} | Light Mode: {data['aesthetic']['is_light_theme']}{Fore.RESET}\n")
        
        for scene in data['scenes']:
            print(f"{Fore.YELLOW}🎬 SCENE {scene['scene_id']} ({scene['duration_seconds']}s){Fore.RESET}")
            print(f"   {Fore.CYAN}Veo Prompt:{Fore.RESET} {scene['veo_prompt']}")
            print(f"   {Fore.GREEN}Voiceover:{Fore.RESET}  {scene['voiceover']}")
            print(f"   {Fore.WHITE}Visual FX:{Fore.RESET}  {scene['visual_fx']}")
            print(f"   {Fore.WHITE}Text Overlay:{Fore.RESET} {scene['kinetic_text']}\n")
            
        print(f"{Fore.GREEN}✅ The AI Brain successfully made all creative decisions autonomously.{Fore.RESET}")

        # Write structured JSON output if --output-json path was given
        if output_json_path:
            import os
            os.makedirs(os.path.dirname(os.path.abspath(output_json_path)), exist_ok=True)
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"{Fore.GREEN}📄 Storyboard JSON written to: {output_json_path}{Fore.RESET}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"{Fore.RED}Error during dry run: {e}{Fore.RESET}")
        sys.exit(1)
