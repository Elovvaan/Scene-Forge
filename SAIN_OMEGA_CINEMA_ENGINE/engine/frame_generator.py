from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List


class FrameGenerator:
    """Generates local MVP start/end frames in the required project shot structure."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.motion_plans: Dict[str, Dict[str, object]] = {}

    def generate_start_end_frames(
        self,
        storyboard_panel: Path,
        shot_dir: Path,
        shot_id: str,
        prompt_context: str,
        previous_end_frame: Path | None = None,
    ) -> Dict[str, Path]:
        try:
            from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
        except ImportError as exc:
            raise RuntimeError('Frame generation requires Pillow. Install requirements.txt.') from exc

        shot_dir.mkdir(parents=True, exist_ok=True)
        source = Image.open(storyboard_panel).convert('RGB')
        canvas = ImageOps.contain(source, (1280, 720), method=Image.Resampling.LANCZOS)
        background = Image.new('RGB', (1280, 720), '#10131a')
        background.paste(canvas, ((1280 - canvas.width) // 2, (720 - canvas.height) // 2))

        start = ImageEnhance.Contrast(ImageEnhance.Color(background).enhance(0.9)).enhance(1.15)
        if previous_end_frame and previous_end_frame.exists():
            previous = Image.open(previous_end_frame).convert('RGB').resize((1280, 720))
            start = Image.blend(previous, start, 0.72)

        end = start.filter(ImageFilter.UnsharpMask(radius=1.4, percent=140, threshold=2))
        end = ImageEnhance.Brightness(end).enhance(0.96)
        vignette = Image.new('RGBA', end.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(vignette)
        w, h = end.size
        for i in range(42):
            alpha = int(i * 1.4)
            draw.rectangle([i, i, w - i, h - i], outline=(0, 0, 0, alpha))
        end = Image.alpha_composite(end.convert('RGBA'), vignette).convert('RGB')

        start_path = shot_dir / 'start_frame.png'
        end_path = shot_dir / 'end_frame.png'
        start.save(start_path)
        end.save(end_path)
        (shot_dir / 'prompt_context.txt').write_text(prompt_context, encoding='utf-8')

        self.motion_plans[shot_id] = {
            'plan': {
                'shot_id': shot_id,
                'camera_move': 'subtle cinematic move',
                'continuity_source': str(previous_end_frame) if previous_end_frame else None,
                'start_frame': str(start_path),
                'end_frame': str(end_path),
            }
        }
        return {'start_frame': start_path, 'end_frame': end_path}

    def generate_candidates(self, panel_path: Path, count: int = 3, shot_id: str | None = None, emotion: str = 'neutral') -> List[Path]:
        # Backward-compatible shim for older callers.
        target_dir = self.output_dir / panel_path.parent.name / panel_path.stem
        frames = self.generate_start_end_frames(panel_path, target_dir, shot_id or panel_path.stem, emotion)
        return [frames['start_frame'], frames['end_frame']][:count]
