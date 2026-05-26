from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from SAIN_OMEGA_CINEMA_ENGINE.engine.depth_engine import DepthAnalysis


@dataclass
class MotionPlan:
    shot_id: str
    camera_move: str
    parallax_strength: float
    focus_target: str
    environment_motion: List[str]
    timing_curve: str
    cinematic_drift: float
    handheld_micro_motion: float
    focus_breathing: float

    def to_dict(self) -> Dict[str, object]:
        return {
            'shot_id': self.shot_id,
            'camera_move': self.camera_move,
            'parallax_strength': round(self.parallax_strength, 3),
            'focus_target': self.focus_target,
            'environment_motion': self.environment_motion,
            'timing_curve': self.timing_curve,
            'cinematic_drift': round(self.cinematic_drift, 3),
            'handheld_micro_motion': round(self.handheld_micro_motion, 3),
            'focus_breathing': round(self.focus_breathing, 3),
        }


class MotionPlanner:
    def build_plan(self, shot_id: str, depth: DepthAnalysis, emotion: str = 'neutral') -> MotionPlan:
        camera_move = self._pick_camera_move(depth)
        base_parallax = 0.14 if depth.visual_weight == 'center' else 0.2
        if emotion in {'tense', 'dramatic'}:
            base_parallax += 0.04
        elif emotion in {'calm', 'warm'}:
            base_parallax -= 0.03

        environment = ['fog_drift']
        environment.append('light_flicker')
        if depth.horizon < 0.3 or depth.horizon > 0.75:
            environment.append('atmospheric_haze')

        return MotionPlan(
            shot_id=shot_id,
            camera_move=camera_move,
            parallax_strength=max(0.08, min(0.32, base_parallax)),
            focus_target=depth.subject_focus,
            environment_motion=environment,
            timing_curve='ease_in_out',
            cinematic_drift=0.018 if depth.visual_weight == 'center' else 0.026,
            handheld_micro_motion=0.006 if emotion in {'calm', 'warm'} else 0.012,
            focus_breathing=0.015 if depth.subject_focus == 'subject_center' else 0.01,
        )

    def _pick_camera_move(self, depth: DepthAnalysis) -> str:
        if depth.subject_focus == 'subject_center':
            return 'slow_push'
        if depth.visual_weight == 'left':
            return 'dolly_right'
        if depth.visual_weight == 'right':
            return 'dolly_left'
        return 'orbit_subtle'
