from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class MotionValidationIssue:
    shot_id: str
    reason: str

    def to_dict(self) -> Dict[str, str]:
        return {'shot_id': self.shot_id, 'reason': self.reason}


class MotionPlanValidator:
    REQUIRED_FIELDS: Tuple[str, ...] = (
        'shot_id',
        'camera_move',
        'parallax_strength',
        'focus_target',
        'timing_curve',
        'environment_motion',
        'cinematic_drift',
        'handheld_micro_motion',
        'focus_breathing',
    )

    def validate_plan(self, plan: Dict[str, object]) -> List[str]:
        reasons: List[str] = []
        for field in self.REQUIRED_FIELDS:
            if field not in plan:
                reasons.append(f'missing required field: {field}')

        if 'parallax_strength' in plan:
            parallax = plan.get('parallax_strength')
            if not isinstance(parallax, (int, float)):
                reasons.append('parallax_strength must be numeric')
            elif float(parallax) < 0.0 or float(parallax) > 1.0:
                reasons.append('parallax_strength must be between 0.0 and 1.0')

        if 'environment_motion' in plan and not isinstance(plan.get('environment_motion'), list):
            reasons.append('environment_motion must be a list')

        return reasons

    def validate_all(self, motion_plans: Dict[str, Dict[str, object]]) -> Dict[str, object]:
        issues: List[MotionValidationIssue] = []
        valid_count = 0

        for key, payload in motion_plans.items():
            plan = payload.get('plan') if isinstance(payload, dict) else None
            if not isinstance(plan, dict):
                issues.append(MotionValidationIssue(shot_id=key, reason='missing plan payload'))
                continue

            reasons = self.validate_plan(plan)
            shot_id = str(plan.get('shot_id', key))
            if reasons:
                for reason in reasons:
                    issues.append(MotionValidationIssue(shot_id=shot_id, reason=reason))
            else:
                valid_count += 1

        return {
            'total': len(motion_plans),
            'valid': valid_count,
            'invalid': len(motion_plans) - valid_count,
            'issues': [issue.to_dict() for issue in issues],
        }
