from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Dict, List


@dataclass
class MotionQualityResult:
    scene_id: str
    overall_score: int
    shots: List[Dict[str, object]]
    output_path: Path


class MotionQualityScorer:
    def score_scene(
        self,
        scene_id: str,
        shot_payloads: List[Dict[str, object]],
        motion_plans: Dict[str, Dict[str, object]],
        temporal_analysis: List[Dict[str, object]],
        output_dir: Path,
    ) -> MotionQualityResult:
        temporal_by_shot = {str(item.get('shot_id', '')): item for item in temporal_analysis}
        shot_scores: List[Dict[str, object]] = []

        expected_frame_count = 4
        for payload in shot_payloads:
            shot_id = str(payload.get('shot_id', Path(str(payload.get('start_frame', 'unknown'))).stem))
            temporal = temporal_by_shot.get(shot_id, {})
            plan = motion_plans.get(shot_id, {}).get('plan', {})

            sequence = [str(f) for f in temporal.get('interpolated_sequence', [])]
            if not sequence:
                sequence = [str(payload.get('start_frame', '')), str(payload.get('target_frame', ''))]

            unique_count = len(set(sequence))
            frame_count = len(sequence)
            duplicates = max(0, frame_count - unique_count)

            frame_count_consistency = max(0.0, 1.0 - (abs(frame_count - expected_frame_count) / max(1, expected_frame_count)))
            temporal_smoothness = 1.0 if temporal.get('smoothing', {}).get('harsh_jump_prevention') else 0.65
            duplicate_penalty = min(1.0, duplicates / max(1, frame_count))
            jump_risk = 0.15 if temporal.get('smoothing', {}).get('visual_snapping_prevention') else 0.45

            horizon_stability = 1.0 if temporal.get('preservation_guards', {}).get('horizon_stability') else 0.7
            camera_momentum_consistency = 1.0 if temporal.get('preservation_guards', {}).get('camera_momentum') else 0.7

            start_frame = str(payload.get('start_frame', ''))
            target_frame = str(payload.get('target_frame', ''))
            start_align = 1.0 if frame_count > 0 and sequence[0] == start_frame else 0.0
            target_align = 1.0 if frame_count > 1 and sequence[-1] == target_frame else 0.0
            start_target_alignment = (start_align + target_align) / 2

            handheld = float(plan.get('handheld_micro_motion', 0.012) or 0.012)
            momentum_modifier = max(0.0, min(1.0, 1.0 - max(0.0, handheld - 0.02) * 8.0))
            camera_momentum_consistency *= momentum_modifier

            score = (
                frame_count_consistency * 16
                + temporal_smoothness * 17
                + (1.0 - duplicate_penalty) * 16
                + (1.0 - jump_risk) * 13
                + horizon_stability * 12
                + camera_momentum_consistency * 14
                + start_target_alignment * 12
            )
            score_int = max(0, min(100, int(round(score))))

            shot_scores.append(
                {
                    'shot_id': shot_id,
                    'score': score_int,
                    'metrics': {
                        'frame_count_consistency': round(frame_count_consistency, 3),
                        'temporal_smoothness': round(temporal_smoothness, 3),
                        'duplicate_frame_penalty': round(duplicate_penalty, 3),
                        'jump_snapping_risk': round(jump_risk, 3),
                        'horizon_stability': round(horizon_stability, 3),
                        'camera_momentum_consistency': round(camera_momentum_consistency, 3),
                        'start_target_frame_alignment': round(start_target_alignment, 3),
                    },
                    'frame_count': frame_count,
                    'unique_frames': unique_count,
                    'duplicate_frames': duplicates,
                }
            )

        overall = int(round(sum(item['score'] for item in shot_scores) / max(1, len(shot_scores))))
        output_path = output_dir / f'{scene_id}_motion_quality.json'
        payload = {
            'scene_id': scene_id,
            'overall_score': overall,
            'shots': shot_scores,
            'status': 'needs_review' if overall < 70 else 'pass',
        }
        output_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')

        return MotionQualityResult(scene_id=scene_id, overall_score=overall, shots=shot_scores, output_path=output_path)
