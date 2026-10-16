import json
import logging
from typing import Optional
from jarvis.ai_content.scripts.config import GOOGLE_API_KEY
from jarvis.ai_content.scripts.providers.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or GOOGLE_API_KEY
        self.model_name = model_name
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai Client: {e}. Falling back to MOCK mode.")
                self.client = None

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Calls Gemini API with structured JSON response.
        If API key is missing or call fails, returns realistic mock JSON.
        """
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config={
                        "system_instruction": system_prompt,
                        "response_mime_type": "application/json"
                    }
                )
                text = response.text.strip()
                return json.loads(text)
            except Exception as e:
                logger.warning(f"Gemini API request failed: {e}. Falling back to mock JSON.")

        # Fallback Mock JSON based on system prompt detection
        return self._generate_mock_fallback(system_prompt, user_prompt)

    def _generate_mock_fallback(self, system_prompt: str, user_prompt: str) -> dict:
        prompt_lower = system_prompt.lower()

        # 1. Creative Director Mock
        if "creative director" in prompt_lower:
            return {
                "brand_analysis": {
                    "industry": "Developer Productivity",
                    "audience_type": "developers",
                    "brand_personality": "Precision, modern, razor-sharp"
                },
                "tone": "authoritative",
                "palette": {
                    "primary": "#6366F1",
                    "secondary": "#0A0A12",
                    "background_type": "dark_mesh"
                },
                "typography_style": "mono_dev",
                "motion_language": "smooth_parallax",
                "music_direction": "ambient_electronic_build",
                "compositor_strategy": "vfx_heavy",
                "narrative_arc": "problem_solution"
            }

        # 2. Content Planner Mock (Conforms to VisualContract schema)
        if "content planner" in prompt_lower:
            return {
                "script_id": "script_dev_01",
                "total_duration": 24.5,
                "tts_script_with_breaks": "Tired of bloated software slowing down your team? <break time=\"500ms\"/> Meet the next evolution of speed. <break time=\"500ms\"/> Ship code 10x faster today.",
                "tts_tone": "authoritative",
                "music_genre": "ambient_electronic_build",
                "energy_curve": "slow_build_to_fast",
                "entities": [
                    {
                        "id": "character_1",
                        "type": "character",
                        "description": "software engineer in dark hoodie at workstation",
                        "persistent": True
                    },
                    {
                        "id": "item_1",
                        "type": "object",
                        "description": "glowing crystalline microchip with holographic circuits",
                        "persistent": True
                    },
                    {
                        "id": "item_2",
                        "type": "object",
                        "description": "custom mechanical keyboard with glowing keycaps",
                        "persistent": True
                    }
                ],
                "scenes_outline": [
                    {
                        "scene_id": "01", 
                        "purpose": "Hook_Problem", 
                        "duration": 4.5, 
                        "voiceover_line": "Tired of bloated software slowing down your team? <break time=\"500ms\"/>",
                        "entity_refs": ["character_1"],
                        "visual_elements": {
                            "characters": ["software engineer in dark hoodie at workstation"],
                            "key_items": ["overheating dual monitors with error logs", "flashing red warning indicators"],
                            "core_action": "Engineer rubs temples in exasperation as red server alerts flash on screens",
                            "visual_setting": "Dark moody server room and workstation with volumetric fog",
                            "camera_move": {
                                "shot_type": "medium_close_up",
                                "movement": "push_in_slow",
                                "speed": "real_time",
                                "focus": "software engineer and red monitor glow"
                            }
                        },
                        "constraints": {
                            "must_preserve": ["dark moody server room", "one software engineer"],
                            "must_not_include": ["bright daylight office", "multiple people"]
                        }
                    },
                    {
                        "scene_id": "02", 
                        "purpose": "Solution_Reveal", 
                        "duration": 5.0, 
                        "voiceover_line": "Meet the next evolution of developer speed.",
                        "entity_refs": ["item_1"],
                        "visual_elements": {
                            "characters": [],
                            "key_items": ["glowing crystalline microchip with holographic circuits"],
                            "core_action": "Microchip levitates and activates with intense violet energy beam",
                            "visual_setting": "Futuristic clean dark studio with purple rim lighting",
                            "camera_move": {
                                "shot_type": "close_up",
                                "movement": "orbit_subtle",
                                "speed": "slow_motion",
                                "focus": "glowing crystalline microchip"
                            }
                        },
                        "constraints": {
                            "must_preserve": ["glowing crystalline microchip", "purple rim lighting"],
                            "must_not_include": ["cluttered wires", "human hands"]
                        }
                    },
                    {
                        "scene_id": "03", 
                        "purpose": "3d_title", 
                        "duration": 4.5, 
                        "voiceover_line": "Engineered for pure performance and flow.",
                        "entity_refs": ["item_1"],
                        "visual_elements": {
                            "characters": [],
                            "key_items": ["high-velocity luminous fiber optic light beams"],
                            "core_action": "Light particles accelerate through dark void into crystalline node",
                            "visual_setting": "Infinite dark cyberspace with cyan and violet light streams",
                            "camera_move": {
                                "shot_type": "wide",
                                "movement": "tracking_dolly",
                                "speed": "ramped",
                                "focus": "converging fiber optic streams"
                            }
                        },
                        "constraints": {
                            "must_preserve": ["cyan and violet light streams", "dark cyberspace"],
                            "must_not_include": ["text overlays in raw footage"]
                        }
                    },
                    {
                        "scene_id": "04", 
                        "purpose": "ui_walkthrough", 
                        "duration": 7.0, 
                        "voiceover_line": "Instant keyboard shortcuts and zero latency.",
                        "entity_refs": ["character_1", "item_2"],
                        "visual_elements": {
                            "characters": ["software engineer in dark hoodie at workstation"],
                            "key_items": ["custom mechanical keyboard with glowing keycaps"],
                            "core_action": "High-speed fluent typing triggering instantaneous command bar actions",
                            "visual_setting": "Warm ambient coding setup with soft background bokeh",
                            "camera_move": {
                                "shot_type": "close_up",
                                "movement": "static",
                                "speed": "real_time",
                                "focus": "hands typing on mechanical keyboard"
                            }
                        },
                        "constraints": {
                            "must_preserve": ["custom mechanical keyboard", "ambient coding setup"],
                            "must_not_include": ["mouse clicking", "laggy screen"]
                        }
                    },
                    {
                        "scene_id": "05", 
                        "purpose": "CTA", 
                        "duration": 3.5, 
                        "voiceover_line": "Start free today. Ship without friction.",
                        "entity_refs": [],
                        "visual_elements": {
                            "characters": [],
                            "key_items": ["floating minimalist 3D brand logo prism"],
                            "core_action": "Logo prism resolves to camera center with dynamic light flare burst",
                            "visual_setting": "Deep space background with expanding gradient horizon",
                            "camera_move": {
                                "shot_type": "medium_wide",
                                "movement": "pull_out",
                                "speed": "real_time",
                                "focus": "center 3D prism"
                            }
                        },
                        "constraints": {
                            "must_preserve": ["deep space background", "expanding gradient horizon"],
                            "must_not_include": ["cluttered background elements"]
                        }
                    }
                ]
            }

        # 3. Storyboard Generator Mock (Conforms to ValidatedStoryboard schema)
        return {
            "storyboard": [
                {
                    "scene_id": "01",
                    "duration": 4.5,
                    "purpose": "Hook_Problem",
                    "veo_prompt": "Cinematic medium close-up of a software engineer in a dark hoodie at a workstation in a dark server room, rubbing temples as red warning indicators flash on dual monitors, slow push-in, volumetric fog, 16:9 photorealistic.",
                    "title": "Stop Fighting Tools",
                    "subtitle": "Complexity kills engineering velocity",
                    "compositor_tag": "vfx_effectcraft",
                    "color_grade": "cold_dev_dark",
                    "camera_move": "push_in_slow",
                    "needs_particles": False,
                    "text_animation": "kinetic_scale_blur",
                    "entity_refs": ["character_1"],
                    "must_preserve": ["dark moody server room", "one software engineer"],
                    "must_not_include": ["bright daylight office", "multiple people"]
                },
                {
                    "scene_id": "02",
                    "duration": 5.0,
                    "purpose": "Solution_Reveal",
                    "veo_prompt": "Slow-motion close-up of a glowing crystalline microchip levitating and activating with a violet energy beam in a dark studio, purple rim lighting, subtle orbital camera move, 16:9 photorealistic.",
                    "title": "Built for Velocity",
                    "subtitle": "Instant sync across entire codebase",
                    "compositor_tag": "vfx_effectcraft",
                    "color_grade": "teal_orange_cinematic",
                    "camera_move": "orbit_subtle",
                    "needs_particles": True,
                    "text_animation": "typewriter",
                    "entity_refs": ["item_1"],
                    "must_preserve": ["glowing crystalline microchip", "purple rim lighting"],
                    "must_not_include": ["cluttered wires", "human hands"]
                },
                {
                    "scene_id": "03",
                    "duration": 4.5,
                    "purpose": "3d_title",
                    "veo_prompt": "Wide tracking dolly shot of luminous cyan and violet fiber optic light beams accelerating through dark cyberspace into a crystalline node, ramped speed, 16:9 photorealistic.",
                    "title": "Zero Latency",
                    "subtitle": "Native speed, unmatched control",
                    "compositor_tag": "vfx_effectcraft",
                    "color_grade": "cold_dev_dark",
                    "camera_move": "push_in_slow",
                    "needs_particles": True,
                    "text_animation": "kinetic_scale_blur",
                    "entity_refs": ["item_1"],
                    "must_preserve": ["cyan and violet light streams", "dark cyberspace"],
                    "must_not_include": ["text overlays in raw footage"]
                },
                {
                    "scene_id": "04",
                    "duration": 7.0,
                    "purpose": "ui_walkthrough",
                    "veo_prompt": "Static close-up of developer hands in a dark hoodie typing fluently at high speed on a custom mechanical keyboard with glowing keycaps, warm ambient studio bokeh, 16:9 photorealistic.",
                    "title": "Keyboard-First Flow",
                    "subtitle": "Every action mapped to command bar",
                    "compositor_tag": "motion_remotion",
                    "color_grade": "warm_neutral",
                    "camera_move": "static",
                    "needs_particles": False,
                    "text_animation": "slide_up",
                    "entity_refs": ["character_1", "item_2"],
                    "must_preserve": ["custom mechanical keyboard", "ambient coding setup"],
                    "must_not_include": ["mouse clicking", "laggy screen"]
                },
                {
                    "scene_id": "05",
                    "duration": 3.5,
                    "purpose": "CTA",
                    "veo_prompt": "Medium-wide pull-out shot of a floating minimalist 3D prism resolving at center frame with a dynamic light flare burst against a deep space gradient horizon, 16:9 photorealistic.",
                    "title": "Supercharge Your Team",
                    "subtitle": "Available on desktop and web",
                    "compositor_tag": "vfx_effectcraft",
                    "color_grade": "teal_orange_cinematic",
                    "camera_move": "pull_out",
                    "needs_particles": True,
                    "text_animation": "kinetic_scale_blur",
                    "entity_refs": [],
                    "must_preserve": ["deep space background", "expanding gradient horizon"],
                    "must_not_include": ["cluttered background elements"]
                }
            ]
        }
