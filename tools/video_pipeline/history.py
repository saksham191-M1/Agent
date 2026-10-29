"""
history.py
──────────
Audit logging and run history tracker for the Director AI video pipeline.
Saves run summaries and creative signatures to maintain variety and prevent repetitive
narrative/primitive patterns.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional


GLOBAL_HISTORY_PATH = Path("history.json")


def record_run_history(
    run_id: str,
    product_name: str,
    domain: str,
    step_name: str,
    metadata: Dict[str, Any]
) -> Path:
    """Records an execution milestone or metric to the run history log."""
    out_dir = Path("out") / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    history_file = out_dir / "history.json"

    history_data: Dict[str, Any] = {
        "run_id": run_id,
        "product_name": product_name,
        "domain": domain,
        "created_at": time.time(),
        "steps": {}
    }

    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history_data = json.load(f)
        except Exception:
            pass

    history_data["steps"][step_name] = {
        "timestamp": time.time(),
        "data": metadata
    }

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=2)

    return history_file


def append_history(signature: Dict[str, Any], history_path: Optional[Path] = None) -> Path:
    """
    Appends a completed ad creative signature to the persistent history file.
    Fields:
      run_id, product_name, narrative_id, scene_count, total_duration_s,
      primitive_sequence, motion_profiles, music_mood, transitions
    """
    target = history_path or GLOBAL_HISTORY_PATH
    history_list: List[Dict[str, Any]] = []

    if target.exists():
        try:
            with open(target, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, list):
                    history_list = content
        except Exception:
            pass

    history_list.append({
        "timestamp": time.time(),
        **signature
    })

    with open(target, "w", encoding="utf-8") as f:
        json.dump(history_list, f, indent=2)

    return target


def get_recent_history(n: int = 5, history_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Returns the last n creative signatures from the history log."""
    target = history_path or GLOBAL_HISTORY_PATH
    if not target.exists():
        return []

    try:
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data[-n:]
    except Exception:
        pass
    return []


def format_history_nudge(signatures: List[Dict[str, Any]]) -> str:
    """Formats recent signatures as a prompt nudge to ensure narrative and visual diversity."""
    if not signatures:
        return ""

    lines = []
    for s in signatures:
        name = s.get("product_name", "Unknown")
        narrative = s.get("narrative_id", "pas")
        prims = ", ".join(s.get("primitive_sequence", [])) or "standard"
        motion = ", ".join(s.get("motion_profiles", [])) or "smooth"
        lines.append(f"- Product '{name}': Narrative={narrative}, Layouts/Primitives=[{prims}], Motion=[{motion}]")

    return (
        "\nRECENT COMPLETED AD SIGNATURES (AVOID REPEATING IDENTICAL NARRATIVE & PRIMITIVE COMBINATIONS):\n"
        + "\n".join(lines)
        + "\nEnsure this new ad introduces fresh pacing, different scene layouts, and unique copy.\n"
    )
