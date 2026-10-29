# Jarvis Video Pipeline V2 Architecture & Operations

## Overview
Jarvis Video Pipeline V2 upgrades the automated ad generation pipeline from a rigid 4-scene template into a flexible, product-specific creative director system. The system dynamically extracts real brand facts, selects optimal narrative arcs, synthesizes audio layers, and renders through Remotion at 1080p 60fps.

---

## Architecture Flow

```
[Target Product URL / Name]
       │
       ▼
1. Playwright Crawl & Brand Extraction (remotion/scripts/scrape-brand.ts)
   ├── Real DOM screenshot & mobile viewport capture
   ├── WCAG 2.1 AA contrast validation (>= 4.5:1 text/bg)
   └── Primary typography extraction with sans-serif fallbacks
       │
       ▼
2. Factuality-Grounded Product Profile (tools/video_pipeline/product_profile.py)
   ├── Director Call 1: Extracts grounded claims and proof points
   └── Deterministic Post-Validation:
       ├── Strips ungrounded statistics, fake ratings, and unextracted prices
       ├── Enforces REAL-OR-NULL policy (zero fake numbers)
       └── Drops hallucinated asset references
       │
       ▼
3. Intelligent Narrative Selection (tools/video_pipeline/narratives.py)
   ├── Narrative Arc Library (tools/video_pipeline/narratives.json)
   │   (Problem-Agitate-Solution, Feature Showcase, Social Proof & Momentum,
   │    Speed & Efficiency, Technical Deep Dive, Before / After Transformation)
   ├── Arc scoring based on category, tone match, and evidence readiness
   └── Penalty mechanism: skips pricing arcs when price is not grounded
       │
       ▼
4. Dynamic Storyboard & Critique Loop (tools/video_pipeline/storyboard_director.py)
   ├── History injection: scans recent signatures from history.json to ensure variety
   ├── Director Call 2: Dynamic multi-scene storyboard generation (3–8 scenes, 10–40s)
   ├── Strict Headline Rules: Terminal punctuation regex `[.:;!?]+$` strictly banned
   ├── Director Call 3 (Critique Gate):
   │   ├── Scores specificity, differentiator use, pacing, and copy quality (1–5)
   │   ├── Quality threshold: Rejects and revisions when specificity or differentiator < 4
   │   └── Verifies zero invented claims and strict grammar
   └── Output: StoryboardDirectorSpec (validated by Pydantic and Zod spec-schema)
       │
       ▼
5. Dynamic Audio Synthesis (audio_layer.py & voices.json)
   ├── Tone-driven voiceover mapping from voices.json (e.g. fast_confident, energetic)
   ├── Dynamic VO offsets calculated per scene duration
   ├── Contextual SFX triggering (whoosh, click, pop, riser, hit)
   └── Audio ducking & loudnorm to EBU R128 (-14 LUFS integrated, -1.5 dBFS true peak)
       │
       ▼
6. Vector UI Assembly & Composable Primitives (remotion/engine/primitives/)
   ├── 9 Modular Primitives:
   │   phone_frame, browser_frame, kinetic_headline, metric_counter,
   │   card_grid, screenshot_pan, logo_reveal, feature_list, quote_card
   ├── Dynamic slot composition: full, left, right, overlay
   └── Fallback handling for resilient rendering
       │
       ▼
7. Remotion 60FPS Video Rendering (remotion/scripts/produce-ad.ts)
   ├── Motion profile interpolation (smooth, snappy, dramatic, playful, technical)
   ├── Camera push scale ranges obeying non-stopping motion rules
   └── Automated 11-gate quality assurance verification suite
```

---

## Schemas & Contracts

### 1. Product Profile Schema (`tools/video_pipeline/schemas.py`)
- `product_name`: string
- `category`: string (ecommerce, devtool, fintech, saas, consumer)
- `tagline`: string
- `target_audience`: string
- `core_value_prop`: string
- `key_features`: list of strings
- `proof_points`: list of `ProofPoint` items (metric, text, source)
- `tone`: string (confident, technical, playful, dramatic, smooth)
- `visual_assets`: list of `AssetRef`
- `missing_data`: list of string markers for missing fields

### 2. Storyboard Director Spec Schema (`tools/video_pipeline/schemas.py`, mirrored in `remotion/scripts/spec-schema.ts`)
- `product_name`: string
- `narrative_type`: string
- `total_seconds`: number (10.0 to 40.0)
- `scene_count`: integer (3 to 8)
- `music_mood`: string
- `voice_style`: string
- `scenes`: array of `SceneDirectorSpec`
  - `scene_id`: integer (1-indexed)
  - `duration_seconds`: number
  - `layout`: string (`hero-type`, `split`, `phone`, `browser`, `card`, `metrics`, `testimonial`, `cta`)
  - `motion_profile`: string (`smooth`, `snappy`, `dramatic`, `playful`, `technical`)
  - `kinetic_text`: headline without terminal punctuation
  - `voiceover`: spoken dialogue
  - `visual_fx`: visual transition/effect
  - `transition_out`: transition preset
  - `requires_ui_image`: boolean

---

## How to Extend the Pipeline

### How to Add a Narrative Arc
1. Open `tools/video_pipeline/narratives.json`.
2. Add a new narrative definition with:
   - `name`: Human-readable title
   - `type`: Unique snake_case identifier
   - `description`: When this arc applies
   - `best_for`: Categories and tones it suits
   - `duration_range`: `[min_seconds, max_seconds]` (within 10–40s)
   - `scene_count_range`: `[min_scenes, max_scenes]` (within 3–8)
   - `scene_blueprints`: Array of scene blueprints with `role`, `recommended_duration`, `allowed_layouts`, `allowed_motion`, and `requires_ui`
3. Run `venv/Scripts/python.exe tools/video_pipeline/test_narratives.py` to verify valid syntax and duration boundaries.

### How to Add a Composable Primitive
1. Open `remotion/engine/primitives/index.tsx`.
2. Implement your component matching the primitive props contract (`theme`, `motion`, `content`, `style`).
3. Register the component in `PRIMITIVE_REGISTRY`.
4. Export the component in `remotion/engine/primitives/index.tsx` and `remotion/engine/index.ts`.
5. Run `npm run verify` in `remotion/` to ensure zero type or export warnings.

### How to Add a Motion Profile
1. Edit `remotion/engine/motion-profiles.json` and `tools/video_pipeline/motion-profiles.json`.
2. Add the profile key (e.g. `cinematic_slow`) with:
   - `camera_push_scale_min`: e.g. `1.0`
   - `camera_push_scale_max`: e.g. `1.04` (must stay above 1.0 to obey non-stopping camera rules)
   - `spring_damping`: number
   - `spring_mass`: number
   - `spring_stiffness`: number
   - `transition_default`: string
3. Run `npm run verify` to test schema adherence.
