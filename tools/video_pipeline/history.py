"""
history.py
──────────
Audit logging and run history tracker for the Director AI video pipeline.
Saves run summaries, tokens, models used, and QA outcomes under out/<run_id>/history.json.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional


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
