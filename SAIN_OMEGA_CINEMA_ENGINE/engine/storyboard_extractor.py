from pathlib import Path
from typing import List

from PIL import Image


class StoryboardExtractor:
    """Automatically extracts storyboard panels using adaptive grid splitting."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def extract_panels(self, sheet_path: Path, cols: int = 3, rows: int = 3) -> List[Path]:
        img = Image.open(sheet_path).convert('RGB')
        w, h = img.size
        panel_w = w // cols
        panel_h = h // rows

        shot_dir = self.output_dir / sheet_path.stem
        shot_dir.mkdir(parents=True, exist_ok=True)

        panels: List[Path] = []
        idx = 1
        for r in range(rows):
            for c in range(cols):
                left = c * panel_w
                top = r * panel_h
                right = w if c == cols - 1 else (c + 1) * panel_w
                bottom = h if r == rows - 1 else (r + 1) * panel_h
                crop = img.crop((left, top, right, bottom))
                panel_path = shot_dir / f'panel_{idx:02d}.png'
                crop.save(panel_path)
                panels.append(panel_path)
                idx += 1
        return panels
