from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

from SAIN_OMEGA_CINEMA_ENGINE.packets.image_synthesis_packet import ImageSynthesisPacket


class FrameSynthesisBridge:
    """Builds structured image synthesis JSON packets from shot + motion + temporal data."""

    POSITIONS: Tuple[float, ...] = (0.15, 0.30, 0.45, 0.60, 0.75, 0.90)

    def build_for_shot(
        self,
        shot_payload: Dict[str, object],
        motion_plan_payload: Dict[str, object] | None,
        temporal_analysis: Dict[str, object] | None,
        synthesis_dir: Path,
    ) -> List[Path]:
        motion_plan_payload = motion_plan_payload or {}
        temporal_analysis = temporal_analysis or {}

        shot_id = str(shot_payload.get('shot_id', 'shot_unknown'))
        scene_id = str(shot_payload.get('scene_id', 'scene_unknown'))
        previous_frame = Path(str(shot_payload['start_frame']))
        target_frame = Path(str(shot_payload['target_frame']))
        emotion = str(shot_payload.get('emotion', 'neutral'))
        tone = str(shot_payload.get('visual_tone', 'cinematic'))

        plan = motion_plan_payload.get('plan', {}) if isinstance(motion_plan_payload, dict) else {}
        camera_move = str(plan.get('camera_move', shot_payload.get('camera_move', 'static')))
        motion_intensity = float(shot_payload.get('motion_intensity', plan.get('parallax_strength', 0.35)))
        timing_curve = str(plan.get('timing_curve', 'ease_in_out'))

        continuity_locks = {
            'continuity_id': shot_payload.get('continuity_id', f'{scene_id}_{shot_id}'),
            'subject_focus': plan.get('focus_target', 'subject_center'),
            'environment_motion': plan.get('environment_motion', []),
            'preservation_guards': temporal_analysis.get('preservation_guards', {}),
            'smoothing': temporal_analysis.get('smoothing', {}),
        }

        prompt = (
            f'{tone} frame interpolation, {emotion} emotional continuity, '
            f'camera move {camera_move}, preserve subject identity and environment details'
        )
        negative_prompt = (
            'no new characters, no scene reset, no lighting jump, no camera-axis flip, '
            'no style drift, no temporal discontinuity'
        )

        packet_paths: List[Path] = []
        for position in self.POSITIONS:
            pct = int(position * 100)
            synthesis_id = f'{shot_id}_synth_{pct:02d}'
            output_frame_path = synthesis_dir / f'{synthesis_id}.png'
            packet = ImageSynthesisPacket(
                synthesis_id=synthesis_id,
                shot_id=shot_id,
                scene_id=scene_id,
                previous_frame=previous_frame,
                target_frame=target_frame,
                temporal_position=position,
                camera_move=camera_move,
                motion_intensity=motion_intensity,
                timing_curve=timing_curve,
                emotion_transition=f'{emotion}_to_{emotion}',
                continuity_locks=continuity_locks,
                preserve_identity=True,
                preserve_environment=True,
                preserve_lighting=True,
                preserve_camera_axis=True,
                prompt=prompt,
                negative_prompt=negative_prompt,
                output_frame_path=output_frame_path,
            )
            packet_paths.append(packet.save_json(synthesis_dir))
        return packet_paths

    def write_manifest(self, scene_id: str, packet_paths: List[Path], output_path: Path) -> Path:
        import json

        output_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            'scene_id': scene_id,
            'positions': list(self.POSITIONS),
            'synthesis_packet_count': len(packet_paths),
            'synthesis_packets': [str(p) for p in packet_paths],
        }
        output_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        return output_path
