from abc import ABC, abstractmethod
from pathlib import Path

class VideoProvider(ABC):
    @abstractmethod
    def generate_clip(
        self, 
        prompt: str, 
        scene_id: str, 
        duration: int = 5,
        aspect_ratio: str = "16:9",
        model_tier: str = "quality"
    ) -> Path:
        """
        Generates a video clip based on the prompt and saves it locally.
        Returns the Path to the generated video file.
        """
        pass
