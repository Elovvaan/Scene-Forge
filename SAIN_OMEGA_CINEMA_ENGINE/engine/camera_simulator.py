from __future__ import annotations

from pathlib import Path
from typing import List

from PIL import Image, ImageEnhance

from SAIN_OMEGA_CINEMA_ENGINE.engine.depth_engine import DepthAnalysis
from SAIN_OMEGA_CINEMA_ENGINE.engine.motion_planner import MotionPlan


class CameraSimulator:
    """Applies subtle cinematic motion simulation while preserving composition."""

    def render_smart_frames(
        self,
        panel_path: Path,
        depth: DepthAnalysis,
        plan: MotionPlan,
        out_dir: Path,
        frame_count: int = 3,
    ) -> List[Path]:
        img = Image.open(panel_path).convert('RGB')
        out_dir.mkdir(parents=True, exist_ok=True)
        frames: List[Path] = []
        for idx in range(frame_count):
            t = 0.0 if frame_count == 1 else idx / (frame_count - 1)
            frame = self._apply_motion(img, depth, plan, t)
            out_path = out_dir / f'candidate_{idx + 1:02d}.png'
            frame.save(out_path)
            frames.append(out_path)
        return frames

    def _apply_motion(self, img: Image.Image, depth: DepthAnalysis, plan: MotionPlan, t: float) -> Image.Image:
        w, h = img.size
        eased = (3 * t * t) - (2 * t * t * t)  # smoothstep
        z_push = 1.0 + (plan.parallax_strength * 0.08 * eased)

        scaled = img.resize((int(w * z_push), int(h * z_push)), Image.Resampling.LANCZOS)
        off_x = max(0, (scaled.width - w) // 2)
        off_y = max(0, (scaled.height - h) // 2)
        base = scaled.crop((off_x, off_y, off_x + w, off_y + h))

        drift_px = int(w * plan.cinematic_drift * (eased - 0.5))
        handheld_px = int(h * plan.handheld_micro_motion * ((-1) ** int(t * 10)))
        focus_gain = 1.0 + (plan.focus_breathing * (0.5 - abs(t - 0.5)))

        moved = Image.new('RGB', (w, h), (0, 0, 0))
        moved.paste(base, (drift_px, handheld_px))
        moved = moved.crop((0, 0, w, h))
        moved = ImageEnhance.Sharpness(moved).enhance(1.0 + plan.parallax_strength * 0.3)
        moved = ImageEnhance.Contrast(moved).enhance(focus_gain)

        if plan.camera_move in {'dolly_right', 'dolly_left'}:
            pan = int(w * 0.012 * eased) * (1 if plan.camera_move == 'dolly_right' else -1)
            pan_canvas = Image.new('RGB', (w, h), (0, 0, 0))
            pan_canvas.paste(moved, (pan, 0))
            moved = pan_canvas.crop((0, 0, w, h))

        return moved
