"""Deterministic editorial beats shared by camera cuts and local sound design."""
import math

from .models import timeline


RENDERER_VERSION = "product-film-3"


def shot_plan(scenes: list[dict]) -> list[dict]:
    """Break long holds into wide/detail/reframe shots, without inventing actions."""
    shots = []
    for index, scene in enumerate(timeline(scenes)):
        # Keep the end card readable; product proof gets the most coverage.
        count = 1 if index == len(scenes) - 1 else max(2, min(4, math.ceil(scene["duration"] / 2)))
        for beat in range(count):
            start = round(scene["start"] + scene["duration"] * beat / count, 4)
            end = round(scene["start"] + scene["duration"] * (beat + 1) / count, 4)
            shots.append({"scene": index, "beat": beat, "start": start, "end": end,
                          "framing": ("wide", "detail", "reframe", "wide")[beat]})
    return shots
