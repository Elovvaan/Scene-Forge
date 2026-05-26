from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageFilter, ImageStat


@dataclass
class DepthAnalysis:
    foreground: Tuple[int, int, int, int]
    midground: Tuple[int, int, int, int]
    background: Tuple[int, int, int, int]
    subject_focus: str
    horizon: float
    lighting_direction: str
    visual_weight: str

    def to_dict(self) -> Dict[str, object]:
        return {
            'foreground': list(self.foreground),
            'midground': list(self.midground),
            'background': list(self.background),
            'subject_focus': self.subject_focus,
            'horizon': round(self.horizon, 3),
            'lighting_direction': self.lighting_direction,
            'visual_weight': self.visual_weight,
        }


class DepthEngine:
    """Heuristic depth and composition inference for storyboard panels."""

    def analyze(self, panel_path: Path) -> DepthAnalysis:
        img = Image.open(panel_path).convert('RGB')
        w, h = img.size

        # Spatial zones to preserve composition while simulating depth.
        foreground = (0, int(h * 0.62), w, h)
        midground = (0, int(h * 0.34), w, int(h * 0.62))
        background = (0, 0, w, int(h * 0.34))

        # Subject focus: highest local variance block is considered focal subject.
        gray = img.convert('L').filter(ImageFilter.FIND_EDGES)
        block_w, block_h = max(24, w // 3), max(24, h // 3)
        best_score = -1.0
        best_xy = (w // 2, h // 2)
        for by in range(0, h, block_h):
            for bx in range(0, w, block_w):
                crop = gray.crop((bx, by, min(w, bx + block_w), min(h, by + block_h)))
                score = ImageStat.Stat(crop).mean[0]
                if score > best_score:
                    best_score = score
                    best_xy = (bx + crop.width // 2, by + crop.height // 2)
        x_norm = best_xy[0] / max(1, w)
        y_norm = best_xy[1] / max(1, h)
        if 0.35 <= x_norm <= 0.65 and 0.3 <= y_norm <= 0.7:
            subject_focus = 'subject_center'
        elif x_norm < 0.35:
            subject_focus = 'subject_left'
        else:
            subject_focus = 'subject_right'

        # Horizon: row with strongest horizontal edge energy.
        edges = gray
        row_sums = [0] * h
        for idx, value in enumerate(edges.getdata()):
            row_sums[idx // w] += value
        strongest_row = max(range(h), key=row_sums.__getitem__)
        horizon = strongest_row / max(1, h - 1)

        left_luma = ImageStat.Stat(img.convert('L').crop((0, 0, w // 2, h))).mean[0]
        right_luma = ImageStat.Stat(img.convert('L').crop((w // 2, 0, w, h))).mean[0]
        lighting_direction = 'left_to_right' if left_luma > right_luma else 'right_to_left'

        third = w // 3
        left_weight = ImageStat.Stat(gray.crop((0, 0, max(1, third), h))).mean[0]
        center_weight = ImageStat.Stat(gray.crop((max(1, third), 0, max(2, third * 2), h))).mean[0]
        right_weight = ImageStat.Stat(gray.crop((max(2, third * 2), 0, w, h))).mean[0]
        if center_weight >= max(left_weight, right_weight):
            visual_weight = 'center'
        elif left_weight > right_weight:
            visual_weight = 'left'
        else:
            visual_weight = 'right'

        return DepthAnalysis(
            foreground=foreground,
            midground=midground,
            background=background,
            subject_focus=subject_focus,
            horizon=horizon,
            lighting_direction=lighting_direction,
            visual_weight=visual_weight,
        )
