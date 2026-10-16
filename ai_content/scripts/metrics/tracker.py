import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.ai_content.scripts.config import METRICS_DIR

logger = logging.getLogger(__name__)

class RunTracker:
    """
    Tracks generation metrics, latency per stage, retry attempts,
    and Google Flow credit expenditure (starting from 1050 credits).
    """
    def __init__(self, run_id: Optional[str] = None, starting_credits: int = 1050):
        self.run_id = run_id or f"run_{int(time.time())}"
        self.starting_credits = starting_credits
        self.credits_remaining = starting_credits
        self.credits_used = 0
        self.stage_timings: Dict[str, float] = {}
        self.scene_metrics: List[Dict[str, Any]] = []
        self.retries: int = 0
        self.start_time = time.time()
        self._current_stage: Optional[str] = None
        self._stage_start_time: float = 0.0

    def start_stage(self, stage_name: str):
        if self._current_stage:
            self.end_stage()
        self._current_stage = stage_name
        self._stage_start_time = time.time()

    def end_stage(self):
        if self._current_stage:
            elapsed = time.time() - self._stage_start_time
            self.stage_timings[self._current_stage] = round(elapsed, 2)
            self._current_stage = None

    def record_scene_generation(
        self,
        scene_id: str,
        compositor_tag: str,
        duration: float,
        model_tier: str = "quality",
        retries: int = 0,
        success: bool = True
    ):
        # Credit costs: quality = 10, flash/lite = 5
        cost = 10 if model_tier == "quality" else 5
        if success:
            self.credits_remaining = max(0, self.credits_remaining - cost)
            self.credits_used += cost
        self.retries += retries

        self.scene_metrics.append({
            "scene_id": scene_id,
            "compositor_tag": compositor_tag,
            "duration": duration,
            "model_tier": model_tier,
            "credit_cost": cost,
            "retries": retries,
            "success": success
        })

    def export_summary(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        self.end_stage()
        total_duration = round(time.time() - self.start_time, 2)

        summary = {
            "run_id": self.run_id,
            "total_execution_time_seconds": total_duration,
            "google_flow_credits": {
                "initial_credits": self.starting_credits,
                "credits_used": self.credits_used,
                "credits_remaining": self.credits_remaining
            },
            "total_retries": self.retries,
            "stage_timings": self.stage_timings,
            "scenes": self.scene_metrics
        }

        save_path = output_path or (METRICS_DIR / f"{self.run_id}_metrics.json")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(json.dumps(summary, indent=2))
        logger.info(f"[RunTracker] Metrics report saved to: {save_path}")
        return summary
