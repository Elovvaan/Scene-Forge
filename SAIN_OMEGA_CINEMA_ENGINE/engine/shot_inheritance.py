from __future__ import annotations

from pathlib import Path
from typing import Dict, List


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


class ShotInheritanceEngine:
    """Build inheritance data between sequential shots for cinematic continuity."""

    def __init__(self) -> None:
        self.active = True

    def build_inheritance_chain(
        self,
        shot_payloads: List[Dict[str, object]],
        motion_plans: Dict[str, Dict[str, object]],
    ) -> Dict[str, object]:
        shots: List[Dict[str, object]] = []
        previous: Dict[str, object] | None = None

        for payload in shot_payloads:
            shot_id = str(payload.get('shot_id', 'unknown_shot'))
            plan = motion_plans.get(shot_id, {}).get('plan', {})

            parallax_strength = float(plan.get('parallax_strength', 0.0))
            cinematic_drift = float(plan.get('cinematic_drift', 0.0))
            handheld_micro_motion = float(plan.get('handheld_micro_motion', 0.0))
            focus_breathing = float(plan.get('focus_breathing', 0.0))
            source_fields = [
                'parallax_strength',
                'cinematic_drift',
                'handheld_micro_motion',
                'focus_breathing',
            ]

            camera_momentum = _clamp(
                parallax_strength * 0.45
                + cinematic_drift * 0.25
                + handheld_micro_motion * 0.2
                + focus_breathing * 0.1,
                0.0,
                1.0,
            )

            if 'motion_intensity' in plan:
                camera_momentum = _clamp(camera_momentum + float(plan.get('motion_intensity', 0.0)) * 0.15, 0.0, 1.0)
                source_fields.append('motion_intensity')

            current = {
                'shot_id': shot_id,
                'emotional_tone': payload.get('emotion', 'neutral'),
                'camera_momentum': round(camera_momentum, 3),
                'source_fields_used_for_momentum': source_fields,
                'computed_camera_momentum': round(camera_momentum, 3),
                'lighting_direction': payload.get('visual_tone', 'cinematic'),
                'motion_intensity': payload.get('motion_intensity', 0.35),
                'spatial_orientation': payload.get('camera_move', 'static'),
                'continuity_chain': payload.get('continuity_id', shot_id),
                'focus_target': Path(str(payload.get('target_frame', 'unknown'))).stem,
            }

            inherits = {
                'previous_horizon_alignment': previous['spatial_orientation'] if previous else None,
                'previous_motion_curve': previous['camera_momentum'] if previous else None,
                'previous_focus_target': previous['focus_target'] if previous else None,
                'previous_camera_movement_trend': previous['spatial_orientation'] if previous else None,
            }

            shots.append(
                {
                    'shot_id': shot_id,
                    'inherits_from': previous['shot_id'] if previous else None,
                    'current': current,
                    'inheritance': inherits,
                }
            )
            previous = current

        return {
            'active': True,
            'shots': shots,
            'total_shots': len(shots),
        }
