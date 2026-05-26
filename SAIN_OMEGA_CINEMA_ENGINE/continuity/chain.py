import json
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import List

from PIL import Image

from SAIN_OMEGA_CINEMA_ENGINE.packets.models import ContinuityState


class ContinuityChain:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def analyze_frame(self, frame_path: Path, shot_index: int) -> ContinuityState:
        img = Image.open(frame_path).convert('RGB').resize((64, 64))
        pixels = list(img.getdata())
        avg = tuple(int(mean([p[i] for p in pixels])) for i in range(3))
        mood = 'tense' if sum(avg) < 260 else 'neutral' if sum(avg) < 430 else 'warm'
        return ContinuityState(
            shot_index=shot_index,
            mood=mood,
            dominant_palette=[avg],
            notes={'source': str(frame_path.name)},
        )

    def persist(self, states: List[ContinuityState]) -> None:
        self.path.write_text(json.dumps([asdict(s) for s in states], indent=2), encoding='utf-8')
