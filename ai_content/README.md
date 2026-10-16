# AI Content Pipeline

Agency-grade AI ad and content generation pipeline combining **Google Flow (Veo 3.1 & Omni 1.1)** with **EffectCraft (Rust-based After Effects compositor)**, **Remotion (React motion graphics)**, an event-based **SFX Beat Engine & Multi-Track Audio Mixer**, and **Machine-Enforced Validation Gates**.

## Architecture & Data Flow

```text
Input Brief (JSON)
       │
       ▼
[Stage 1: Creative Director - Gemini 2.5 Pro]   ──> Style, Palette, Motion Language
       │
       ▼
[Stage 2: Content Planner - Gemini 2.5 Flash]    ──> Visual Contract (Entities, Script, Camera moves, Constraints)
       │
       ▼  [Validation Gate 1: Visual Contract Validator]
       │
[Stage 3: Storyboard Generator - Gemini 2.5 Flash] ──> Veo Prompts & Compositor Routing tags
       │
       ▼  [Validation Gate 2: Storyboard Validator]
       │
       ├───> [Stage 4: Audio Engine]
       │         ├──> SFX Beat Engine v2 (Derives cues from core actions)
       │         └──> Multi-Track Audio Mixer (VO + SFX + Ducked Ambient Pad -> master_soundtrack.wav)
       │
       ├───> [Stage 5: Generative Video & Compositing]
       │         ├──> Google Flow Automation (Veo 3.1 via Playwright)
       │         ▼  [Validation Gate 3: Post-Generation Quality Check (ffprobe)]
       │         └──> Compositor Router
       │                   ├──> [vfx_effectcraft]  ──> .ecproj Builder + EffectCraft CLI / ffmpeg fallback
       │                   └──> [motion_remotion]  ──> React Motion / ffmpeg fallback
       │
       ▼
[Stage 6: Master Assembly] ──> ffmpeg Muxer (Video + Master Audio) ──> final_ad.mp4
       │
       ▼
[RunTracker Metrics] ──> Cost, 1050 Credit Balance, Latency & Retries ──> metrics/run_*_metrics.json
```

## Directory Structure
```text
jarvis/ai_content/
├── README.md
├── requirements.txt
├── .env
├── input/
│   └── test_brief.json
├── output/
│   ├── renders/
│   │   ├── raw/                  # Downloaded raw Veo 3.1 clips
│   │   └── final/                # Composited scenes and final_ad.mp4
│   ├── temp_ecproj/              # Generated .ecproj JSON project files
│   ├── audio/                    # Voiceover lines, synthesized SFX, and master_soundtrack.wav
│   └── metrics/                  # Run execution reports (credit usage, latency, retries)
├── prompts/
│   ├── system_prompts.md         # Director, Planner, Storyboard prompts
│   ├── effectcraft_templates.md  # Template references
│   └── templates/                # 4 Core EffectCraft JSON templates
│       ├── template_title_card.json
│       ├── template_video_overlay.json
│       ├── template_3d_text.json
│       └── template_cta_sting.json
├── tests/
│   └── test_pipeline.py          # 7 unit & integration tests covering the full pipeline
└── scripts/
    ├── config.py                 # Centralized paths and environment configs
    ├── pipeline.py               # Master pipeline orchestrator & MasterAssembly
    ├── models/
    │   ├── visual_contract.py    # Pydantic v2 schemas for VisualContract, CameraMove, Entity, Constraints
    │   └── storyboard_contract.py # Pydantic v2 schemas for ValidatedStoryboard
    ├── validators/
    │   └── contract_validator.py # Gates 1, 2, and 3 (Contract, Storyboard, Post-Gen Video)
    ├── audio/
    │   ├── sfx_beat_engine.py    # Event-to-SFX mapping & AudioMixPlan generator
    │   └── audio_mixer.py        # Procedural SFX synth, VO timing, ducked music & FinalSyncValidator
    ├── metrics/
    │   └── tracker.py            # Latency, Google Flow credits (1050 initial), and retry tracker
    ├── tools/
    │   └── setup_flow_session.py # Interactive visible-browser Google Flow login & cookie bootstrapper
    ├── providers/
    │   ├── llm_provider.py       # LLM interface
    │   ├── gemini_provider.py    # Google GenAI with fallback mock JSON
    │   └── omni_provider.py      # Playwright Omni 1.1 stub
    ├── video/
    │   ├── base_video.py         # Video provider interface
    │   └── google_flow_automation.py # Playwright Google Flow (Veo 3.1) automation
    └── compositors/
        ├── base_compositor.py    # Compositor interface
        ├── ecproj_builder.py     # Pydantic Ecproj model + variable injector
        ├── effectcraft_engine.py # EffectCraft CLI executor with ffmpeg fallback
        └── remotion_engine.py    # Remotion executor with fallback
```

## Testing & Execution

### 1. Run Complete Test Suite
```bash
python -m unittest jarvis/ai_content/tests/test_pipeline.py -v
```

### 2. Run Pipeline (Mock Mode)
```bash
python -m jarvis.ai_content.scripts.pipeline --brief jarvis/ai_content/input/test_brief.json --mock
```

### 3. Bootstrap Google Flow Login (When ready for live generation)
```bash
python -m jarvis.ai_content.scripts.tools.setup_flow_session
```
