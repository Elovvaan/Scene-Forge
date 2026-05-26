from pathlib import Path
from typing import List

from PIL import Image


class FrameSequencer:
    def sequence(self, candidate_paths: List[Path], output_dir: Path) -> List[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        sequence: List[Path] = []
        for i, src in enumerate(candidate_paths, start=1):
            img = Image.open(src).convert('RGB')
            out = output_dir / f'frame_{i:04d}.png'
            img.save(out)
            sequence.append(out)
        return sequence
