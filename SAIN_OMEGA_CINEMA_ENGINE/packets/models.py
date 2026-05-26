from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class StoryPacket:
    title: str
    story_text: str


@dataclass
class StoryboardPacket:
    sheet_path: Path
    panels: List[Path] = field(default_factory=list)


@dataclass
class ShotPacket:
    panel_path: Path
    frame_candidates: List[Path] = field(default_factory=list)


@dataclass
class ContinuityState:
    shot_index: int
    mood: str
    dominant_palette: List[tuple]
    notes: Dict[str, str]
