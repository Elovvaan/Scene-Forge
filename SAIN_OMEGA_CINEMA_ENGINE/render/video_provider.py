from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict

from SAIN_OMEGA_CINEMA_ENGINE.render.video_assembler import VideoAssembler


class VideoProvider(ABC):
    """Replaceable provider contract for Kling, Runway, or future video models."""

    @abstractmethod
    def generate_video(self, start_frame: Path, end_frame: Path, shot_context: Dict[str, object]) -> Path:
        raise NotImplementedError


class LocalPreviewVideoProvider(VideoProvider):
    """Offline MVP provider that creates a simple MP4 clip from start/end frames."""

    def __init__(self, assembler: VideoAssembler | None = None) -> None:
        self.assembler = assembler or VideoAssembler()

    def generate_video(self, start_frame: Path, end_frame: Path, shot_context: Dict[str, object]) -> Path:
        output_dir = Path(str(shot_context['output_dir']))
        output_dir.mkdir(parents=True, exist_ok=True)
        duration = float(shot_context.get('duration_seconds', 3.0))
        fps = int(shot_context.get('fps', 8))
        return self.assembler.assemble_clip(start_frame, end_frame, output_dir / 'clip.mp4', duration_seconds=duration, fps=fps)
