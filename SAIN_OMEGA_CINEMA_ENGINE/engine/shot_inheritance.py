from __future__ import annotations

from pathlib import Path
from typing import Dict, List


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
            plan = motion_plans.get(shot_id, {}).get('plan', {}) if isinstance(motion_plans.get(shot_id), dict) else {}

            current = {
                'shot_id': shot_id,
                'emotional_tone': payload.get('emotion', 'neutral'),
                'camera_momentum': plan.get('velocity', 0.35),
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
