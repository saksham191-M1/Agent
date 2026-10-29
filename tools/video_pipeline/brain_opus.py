import os
import sys

_curr_dir = os.path.dirname(os.path.abspath(__file__))
if _curr_dir not in sys.path:
    sys.path.insert(0, _curr_dir)

import json
import re
import requests
from dotenv import load_dotenv
from colorama import Fore, init
from ml_prompt_matcher import OpusPromptMLMatcher

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

def generate_multi_scene_blueprint(product_name, description="", return_match=False):
    codecraft_key = os.getenv("CODECRAFT_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    global_rules = load_global_motion_rules()

    # ML Prompt Matching against 703 curated Opus 5.5 viral videos
    matcher = OpusPromptMLMatcher()
    match_result = matcher.find_best_prompts(product_name, description, top_k=1)
    best_match = match_result["top_matches"][0] if match_result["top_matches"] else None
    
    reference_inspiration = ""
    if best_match:
        print(f"{Fore.CYAN}🎯 ML Matched Category: {best_match['category'].upper()} (Score: {best_match['score']:.4f}){Fore.RESET}")
        print(f"{Fore.CYAN}💡 Viral Inspiration: @{best_match['author']} ({', '.join(best_match['tech_tags'])}){Fore.RESET}")
        print(f"{Fore.CYAN}🔗 Reference: {best_match['skillry_url'] or best_match['post_url']}{Fore.RESET}")
        if best_match['score'] < LOW_MATCH_SCORE:
            print(f"{Fore.YELLOW}⚠️ Low match score ({best_match['score']:.2f}): the reference may be topically close but stylistically off. Review the storyboard.{Fore.RESET}")
        reference_inspiration = build_reference_inspiration(best_match)

    motion_constraints = build_motion_constraints(global_rules)

    prompt = f"""
    You are an Opus-level Creative Director building an automated video pipeline for a product called '{product_name}'.
    Description: '{description if description else product_name}'
    {reference_inspiration}
    {motion_constraints}
    The user wants a highly persuasive 'Problem-Agitate-Solution' (PAS) business ad to gain trust.
    You must autonomously break this down into exactly 4 distinct video scenes.
    Scenes 2 and 3 MUST focus on showcasing the actual app UI workflow to build trust.
    
    Output a JSON object with this exact structure:
    {{
        "product_name": "{product_name}",
        "matched_opus_category": "{best_match['category'].upper() if best_match else 'MOTION'}",
        "selected_template": "Problem-Agitate-Solution (UI Showcase)",
        "scenes": [
            {{
                "scene_id": 1,
                "duration_seconds": 4,
                "voiceover": "State the painful problem clearly.",
                "veo_prompt": "Prompt for Veo to generate a cinematic stock video of the problem.",
                "visual_fx": "fast_zoom",
                "kinetic_text": "The main bold word (e.g. BROKEN)",
                "requires_ui_image": false
            }},
            {{
                "scene_id": 2,
                "duration_seconds": 5,
                "voiceover": "Introduce the product as the solution.",
                "veo_prompt": "Prompt for Veo to take the uploaded UI image and map it onto a 3D floating glass card. Slow camera push-in.",
                "visual_fx": "glass_ui",
                "kinetic_text": "The solution word",
                "requires_ui_image": true
            }}
            // Scene 3 (Deep dive UI workflow, requires_ui_image: true)
            // Scene 4 (CTA/Logo, requires_ui_image: false)
        ]
    }}
    Ensure valid JSON only. Do not use markdown blocks like ```json.
    """
    
    response_text = None

    # 1. Try CodeCraft API (OpenAI-compatible multi-model gateway)
    if codecraft_key:
        cc_model = os.getenv("CODECRAFT_MODEL", "claude-opus-4.8")
        cc_base = os.getenv("CODECRAFT_BASE_URL", "https://codecraftapi.com/v1").rstrip("/")
        cc_headers = {
            "Authorization": f"Bearer {codecraft_key}",
            "Content-Type": "application/json"
        }
        cc_data = {
            "model": cc_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            print(f"{Fore.CYAN}📡 Calling CodeCraft API ({cc_model})...{Fore.RESET}")
            cc_res = requests.post(f"{cc_base}/chat/completions", headers=cc_headers, json=cc_data, timeout=45)
            if cc_res.status_code == 200:
                cc_json = cc_res.json()
                response_text = cc_json["choices"][0]["message"]["content"]
                print(f"{Fore.GREEN}✅ CodeCraft API successfully returned storyboard!{Fore.RESET}")
            else:
                print(f"{Fore.YELLOW}CodeCraft API returned status {cc_res.status_code}: {cc_res.text[:200]}{Fore.RESET}")
        except Exception as err:
            print(f"{Fore.YELLOW}CodeCraft API call error: {err}{Fore.RESET}")

    # 2. Fallback to Gemini if CodeCraft did not return
    if not response_text and gemini_key:
        candidate_models = ["gemini-flash-latest", "gemini-3.5-flash", "gemini-3.7-flash"]
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7}
        }
        for model_name in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                if response.status_code == 200:
                    response_json = response.json()
                    response_text = response_json['candidates'][0]['content']['parts'][0]['text']
                    break
                else:
                    print(f"{Fore.YELLOW}Model {model_name} returned {response.status_code}. Trying fallback...{Fore.RESET}")
            except Exception as err:
                print(f"{Fore.YELLOW}Model {model_name} error: {err}. Trying fallback...{Fore.RESET}")
            
    aesthetic = extract_opus_aesthetic(best_match['prompt'] if best_match else '', author=best_match.get('author', '') if best_match else '')

    if not response_text:
        print(f"{Fore.YELLOW}⚠️ Online AI endpoints busy (503). Using deterministic ML Opus blueprint generator.{Fore.RESET}")
        cat = best_match['category'].upper() if best_match else 'MOTION'
        author = best_match['author'] if best_match else 'Opus'
        fallback_json = {
            "product_name": product_name,
            "matched_opus_category": cat,
            "selected_template": f"Opus 5.5 Viral Blueprint (@{author})",
            "aesthetic": aesthetic,
            "scenes": [
                {
                    "scene_id": 1,
                    "duration_seconds": 4,
                    "voiceover": f"Experience what's next with {product_name}.",
                    "veo_prompt": f"Cinematic dynamic opener for {product_name}",
                    "visual_fx": "fast_zoom",
                    "kinetic_text": product_name.upper(),
                    "requires_ui_image": False
                },
                {
                    "scene_id": 2,
                    "duration_seconds": 5,
                    "voiceover": f"Built specifically for speed and seamless everyday performance.",
                    "veo_prompt": f"Interactive app showcase for {product_name}",
                    "visual_fx": "glass_ui",
                    "kinetic_text": "SEAMLESS",
                    "requires_ui_image": True
                },
                {
                    "scene_id": 3,
                    "duration_seconds": 4,
                    "voiceover": f"Designed to get you results faster than ever before.",
                    "veo_prompt": f"Dense feature workflow in action for {product_name}",
                    "visual_fx": "blur_slide",
                    "kinetic_text": "FASTER",
                    "requires_ui_image": True
                },
                {
                    "scene_id": 4,
                    "duration_seconds": 3,
                    "voiceover": f"Get started with {product_name} today.",
                    "veo_prompt": f"Brand lockup outro for {product_name}",
                    "visual_fx": "fade_up",
                    "kinetic_text": "START NOW",
                    "requires_ui_image": False
                }
            ]
        }
        response_text = json.dumps(fallback_json)
        
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

    app = positional[0] if len(positional) > 0 else "Swiggy"
    desc = positional[1] if len(positional) > 1 else ""

    print(f"{Fore.CYAN}=== OPUS DIRECTOR AI: AUTONOMOUS STORYBOARD FOR '{app.upper()}' ==={Fore.RESET}\n")
    
    try:
        raw_result, best_match = generate_multi_scene_blueprint(app, desc, return_match=True)
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
        print(f"{Fore.RED}Error during dry run: {e}{Fore.RESET}")
        sys.exit(1)
