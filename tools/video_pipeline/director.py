"""
director.py
───────────
The single gateway for all AI Director model calls in the Jarvis video pipeline.
Enforces:
- Schema validation via Pydantic (fail-fast with retries)
- Pluggable provider adapters (OpenAI-compatible CodeCraft / Google Gemini)
- JSON code fence stripping
- Full prompt & response logging with key redaction
- Deterministic mock mode (DIRECTOR_MOCK=1) for offline testing
- Strict error propagation via DirectorError
"""

import os
import re
import json
import time
from pathlib import Path
from typing import Type, TypeVar, Optional, Dict, Any, Callable
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class DirectorError(Exception):
    """Raised when the Director AI Gateway fails after all retries."""
    pass


def clean_json_string(raw: str) -> str:
    """Strips markdown code fences (```json ... ```) and extracts bare JSON string."""
    text = raw.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def redact_secrets(text: str) -> str:
    """Redacts potential API keys and tokens from logs."""
    # Redact Authorization headers or key params
    text = re.sub(r'(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{8,}', r'\1[REDACTED]', text)
    text = re.sub(r'(?i)(key=)[a-zA-Z0-9_\-\.]{8,}', r'\1[REDACTED]', text)
    text = re.sub(r'(?i)(api[_-]?key["\']?\s*[:=]\s*["\'])[a-zA-Z0-9_\-\.]{8,}(["\'])', r'\1[REDACTED]\2', text)
    return text


def _get_log_dir(run_id: Optional[str] = None) -> Path:
    base = Path("out") / (run_id if run_id else "default") / "director_log"
    base.mkdir(parents=True, exist_ok=True)
    return base


# ──────────────────────────────────────────────────────────────────────────────
# Provider Adapters
# ──────────────────────────────────────────────────────────────────────────────

def openai_adapter(
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    timeout: int = 120
) -> str:
    """Adapter for OpenAI-compatible gateways (e.g. CodeCraft, Groq, OpenRouter)."""
    import requests
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise DirectorError(f"OpenAI endpoint ({url}) returned status {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices or "message" not in choices[0]:
        raise DirectorError(f"Unexpected OpenAI response shape: {data}")
    return choices[0]["message"].get("content", "")


def gemini_adapter(
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    timeout: int = 120
) -> str:
    """Adapter for Google Gemini Generative Language API with fast model fallback."""
    import requests
    clean_model = model.replace("models/", "")
    
    # Fast candidate model list (in priority order)
    candidate_models = [clean_model]
    for fallback in ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    headers = {"Content-Type": "application/json"}
    combined_prompt = (
        f"System Instructions:\n{system_prompt}\n\n"
        f"User Request:\n{user_prompt}\n\n"
        f"IMPORTANT: Return ONLY a valid JSON object matching the requested schema. No code fences."
    )
    payload = {
        "contents": [
            {
                "parts": [{"text": combined_prompt}]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json"
        }
    }

    last_err = None
    for m in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    continue
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts or "text" not in parts[0]:
                    continue
                return parts[0]["text"]
            elif resp.status_code in (404, 503, 500, 429):
                last_err = f"Model {m} status {resp.status_code}: {resp.text[:200]}"
                continue
            else:
                raise DirectorError(f"Gemini endpoint returned status {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            last_err = str(e)
            continue

    raise DirectorError(f"All Gemini models exhausted. Last error: {last_err}")


# ──────────────────────────────────────────────────────────────────────────────
# Mock Provider
# ──────────────────────────────────────────────────────────────────────────────

def _generate_mock_response(schema: Type[T], user_prompt: str) -> str:
    """Generates canned, schema-valid JSON for offline testing."""
    name = schema.__name__

    if name == "ToyTestSchema":
        return json.dumps({
            "headline": "TEST PRODUCT LAUNCH",
            "rating": 4.9,
            "tags": ["fast", "verified", "reliable"],
            "is_valid": True
        })

    if name == "ProductProfile":
        return json.dumps({
            "name": "Acme Cloud",
            "what_it_is": "Serverless cloud runtime for modern developers",
            "audience": "Software engineers and DevOps teams",
            "core_differentiator": "Sub-millisecond cold starts with zero configuration",
            "tone": "technical",
            "category": "developer_tools",
            "visual_style_hint": "dark, clean monospace typography",
            "proof_points": [
                {"text": "Zero-latency edge replication", "source": "hero section"},
                {"text": "100k+ active deployments", "source": "metrics counter"}
            ],
            "visual_assets_available": ["studio-hero.png", "studio-mobile.png"],
            "missing_data": ["pricing_tier_annual"],
            "language": "en"
        })

    if name == "StoryboardDirectorSpec":
        return json.dumps({
            "product_name": "Acme Cloud",
            "narrative_type": "technical_walkthrough",
            "scene_count": 4,
            "total_seconds": 16.0,
            "music_mood": "ambient_electronic",
            "voice_style": "confident_engineer",
            "scenes": [
                {
                    "scene_id": 1,
                    "duration_seconds": 4.0,
                    "layout": "hero-type",
                    "motion_profile": "technical",
                    "voiceover": "Deploy serverless backends in milliseconds.",
                    "kinetic_text": "ZERO LATENCY",
                    "visual_fx": "fast_zoom",
                    "transition_out": "carousel_glide",
                    "requires_ui_image": False
                },
                {
                    "scene_id": 2,
                    "duration_seconds": 4.0,
                    "layout": "browser",
                    "motion_profile": "smooth",
                    "voiceover": "Instant global replication on push.",
                    "kinetic_text": "GIT PUSH",
                    "visual_fx": "glass_ui",
                    "transition_out": "wipe",
                    "requires_ui_image": True
                },
                {
                    "scene_id": 3,
                    "duration_seconds": 4.0,
                    "layout": "big-number",
                    "motion_profile": "punchy",
                    "voiceover": "Over 100,000 teams trust Acme for uptime.",
                    "kinetic_text": "100K TEAMS",
                    "visual_fx": "counter_slam",
                    "transition_out": "carousel_glide",
                    "requires_ui_image": False
                },
                {
                    "scene_id": 4,
                    "duration_seconds": 4.0,
                    "layout": "cta",
                    "motion_profile": "minimal",
                    "voiceover": "Start building for free at acme.dev today.",
                    "kinetic_text": "SHIP TODAY",
                    "visual_fx": "fade_up",
                    "transition_out": "none",
                    "requires_ui_image": False
                }
            ]
        })

    # Default fallback using schema field defaults/constructors
    try:
        sample = {}
        for f_name, f_info in schema.model_fields.items():
            if f_info.default is not None:
                sample[f_name] = f_info.default
            elif f_info.annotation == str:
                sample[f_name] = f"sample_{f_name}"
            elif f_info.annotation in (int, float):
                sample[f_name] = 1
            elif f_info.annotation == bool:
                sample[f_name] = True
            elif getattr(f_info.annotation, "__origin__", None) == list:
                sample[f_name] = []
            else:
                sample[f_name] = None
        return json.dumps(sample)
    except Exception as e:
        raise DirectorError(f"Cannot generate mock for {schema}: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Core Gateway Function
# ──────────────────────────────────────────────────────────────────────────────

def call_director(
    system: str,
    user: str,
    schema: Type[T],
    retries: int = 2,
    temperature: float = 0.8,
    step_name: str = "director",
    run_id: Optional[str] = None,
    mock_override: Optional[bool] = None
) -> T:
    """
    Calls the Opus-class Creative Director model, validates output against schema,
    and returns a fully parsed Pydantic model instance.
    """
    is_mock = os.getenv("DIRECTOR_MOCK", "0") == "1" if mock_override is None else mock_override

    # Resolve active API credentials and provider
    api_key = os.getenv("DIRECTOR_API_KEY")
    base_url = os.getenv("DIRECTOR_BASE_URL")
    model = os.getenv("DIRECTOR_MODEL")

    adapter_func: Callable[..., str] = openai_adapter

    if not is_mock:
        if not api_key:
            # Fallback discovery order: GEMINI_API_KEY -> CODECRAFT_API_KEY
            if os.getenv("GEMINI_API_KEY"):
                api_key = os.getenv("GEMINI_API_KEY")
                model = model or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
                base_url = base_url or "https://generativelanguage.googleapis.com"
                adapter_func = gemini_adapter
            elif os.getenv("CODECRAFT_API_KEY"):
                api_key = os.getenv("CODECRAFT_API_KEY")
                model = model or os.getenv("CODECRAFT_MODEL") or "claude-opus-5.5"
                base_url = base_url or os.getenv("CODECRAFT_BASE_URL", "https://codecraftapi.com/v1")
                adapter_func = openai_adapter
            else:
                raise DirectorError(
                    "Missing DIRECTOR_API_KEY (or GEMINI_API_KEY / CODECRAFT_API_KEY) in environment. "
                    "Set DIRECTOR_API_KEY or set DIRECTOR_MOCK=1 for offline execution."
                )
        else:
            # If DIRECTOR_API_KEY was supplied directly, choose adapter by URL or default to openai_adapter
            base_url = base_url or os.getenv("CODECRAFT_BASE_URL", "https://codecraftapi.com/v1")
            model = model or "claude-opus-5.5"
            if "generativelanguage.googleapis.com" in base_url or "gemini" in model.lower():
                adapter_func = gemini_adapter
            else:
                adapter_func = openai_adapter

    log_dir = _get_log_dir(run_id)
    current_user_prompt = user
    last_error_message = ""
    last_raw_response = ""

    for attempt in range(1, retries + 2):
        # 1. Log Prompt
        prompt_log_file = log_dir / f"{step_name}_{attempt}_prompt.txt"
        with open(prompt_log_file, "w", encoding="utf-8") as f:
            f.write(redact_secrets(f"SYSTEM:\n{system}\n\nUSER:\n{current_user_prompt}\n"))

        # 2. Execute Model Call or Mock
        raw_text = ""
        call_error = None
        for backoff in [0.0, 1.0, 2.0, 4.0]:
            if backoff > 0:
                time.sleep(backoff)
            try:
                if is_mock:
                    raw_text = _generate_mock_response(schema, current_user_prompt)
                else:
                    raw_text = adapter_func(
                        base_url=base_url,
                        api_key=api_key,
                        model=model,
                        system_prompt=system,
                        user_prompt=current_user_prompt,
                        temperature=temperature,
                        timeout=120
                    )
                call_error = None
                break
            except Exception as e:
                call_error = e
                # Check for rate limit or server error to trigger backoff
                err_str = str(e)
                if "429" in err_str or "500" in err_str or "503" in err_str:
                    continue
                else:
                    break

        if call_error:
            last_error_message = f"API call failed: {call_error}"
            # Retry loop continues
            current_user_prompt = (
                f"{user}\n\n"
                f"[PREVIOUS ATTEMPT FAILED WITH ERROR]\n{last_error_message}\n\n"
                f"Please output strictly valid JSON matching the schema."
            )
            continue

        # 3. Log Response
        resp_log_file = log_dir / f"{step_name}_{attempt}_response.json"
        with open(resp_log_file, "w", encoding="utf-8") as f:
            f.write(redact_secrets(raw_text))

        last_raw_response = raw_text

        # 4. Clean JSON and Parse Schema
        cleaned = clean_json_string(raw_text)
        try:
            parsed_data = json.loads(cleaned)
        except json.JSONDecodeError as jde:
            last_error_message = f"JSON parse error: {jde}"
            current_user_prompt = (
                f"{user}\n\n"
                f"[PREVIOUS ATTEMPT RETURNED INVALID JSON]\n"
                f"Exact JSON parser error: {jde}\n"
                f"Previous output was:\n{raw_text}\n\n"
                f"Ensure you return ONLY a raw JSON string without syntax errors."
            )
            continue

        try:
            validated_model = schema.model_validate(parsed_data)
            # Success!
            return validated_model
        except ValidationError as ve:
            last_error_message = f"Schema validation error: {ve}"
            current_user_prompt = (
                f"{user}\n\n"
                f"[PREVIOUS ATTEMPT FAILED SCHEMA VALIDATION]\n"
                f"Exact validation errors:\n{ve}\n\n"
                f"Previous output was:\n{cleaned}\n\n"
                f"Please fix all schema violations and return the corrected JSON."
            )
            continue

    # If all attempts exhausted
    raise DirectorError(
        f"Director Gateway failed after {retries + 1} attempts for step '{step_name}'.\n"
        f"Last Error: {last_error_message}\n"
        f"Last Raw Output: {last_raw_response[:500]}"
    )
