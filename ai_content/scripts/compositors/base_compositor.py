from abc import ABC, abstractmethod
from pathlib import Path

class BaseCompositor(ABC):
    @abstractmethod
    def render(self, scene_data: dict, asset_path: Path) -> Path:
        """
        Renders a composite scene given scene metadata and input raw video asset.
        Returns the Path to the rendered scene video.
        """
        pass
