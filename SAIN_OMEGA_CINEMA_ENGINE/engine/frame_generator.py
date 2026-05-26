from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw
from SAIN_OMEGA_CINEMA_ENGINE.engine.camera_simulator import CameraSimulator
from SAIN_OMEGA_CINEMA_ENGINE.engine.depth_engine import DepthEngine
from SAIN_OMEGA_CINEMA_ENGINE.engine.motion_planner import MotionPlanner


class FrameGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.depth_engine = DepthEngine()
        self.motion_planner = MotionPlanner()
        self.camera_simulator = CameraSimulator()
        self.motion_plans: Dict[str, Dict[str, object]] = {}

    def generate_candidates(self, panel_path: Path, count: int = 3, shot_id: str | None = None, emotion: str = 'neutral') -> List[Path]:
        img = Image.open(panel_path).convert('RGB')
        shot_name = panel_path.stem
        target_dir = self.output_dir / panel_path.parent.name / shot_name
        target_dir.mkdir(parents=True, exist_ok=True)
        depth = self.depth_engine.analyze(panel_path)
        motion_plan = self.motion_planner.build_plan(shot_id=shot_id or shot_name, depth=depth, emotion=emotion)
        self.motion_plans[motion_plan.shot_id] = {
            'depth': depth.to_dict(),
            'plan': motion_plan.to_dict(),
        }

        smart_frames = self.camera_simulator.render_smart_frames(
            panel_path=panel_path,
            depth=depth,
            plan=motion_plan,
            out_dir=target_dir,
            frame_count=min(count, 3),
        )
        if count <= 3:
            return smart_frames

        variants = [
            self._cinematic_grade(img),
            self._contrast_push(img),
            self._dramatic_vignette(img),
        ]

        results: List[Path] = list(smart_frames)
        for i, variant in enumerate(variants[: max(0, count - len(results))], start=len(results) + 1):
            out_path = target_dir / f'candidate_{i:02d}.png'
            variant.save(out_path)
            results.append(out_path)
        return results

    def _cinematic_grade(self, img: Image.Image) -> Image.Image:
        c = ImageEnhance.Color(img).enhance(0.85)
        b = ImageEnhance.Brightness(c).enhance(0.95)
        return ImageEnhance.Contrast(b).enhance(1.25)

    def _contrast_push(self, img: Image.Image) -> Image.Image:
        sharp = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=2))
        return ImageEnhance.Contrast(sharp).enhance(1.4)

    def _dramatic_vignette(self, img: Image.Image) -> Image.Image:
        gray = ImageOps.grayscale(img)
        tinted = ImageOps.colorize(gray, black='#101320', white='#d6d2ca')
        overlay = Image.new('RGBA', tinted.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        w, h = tinted.size
        for i in range(20):
            alpha = int(6 + i * 2.5)
            draw.rectangle([i, i, w - i, h - i], outline=(0, 0, 0, alpha))
        return Image.alpha_composite(tinted.convert('RGBA'), overlay).convert('RGB')
