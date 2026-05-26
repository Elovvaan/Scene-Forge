from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class SynthesisPacketValidator:
    """Validates image synthesis packet payloads and persists scene-level reports."""

    def validate_packets(self, scene_id: str, packet_paths: List[Path], output_dir: Path) -> Dict[str, Any]:
        issues: List[Dict[str, str]] = []

        for packet_path in packet_paths:
            payload = json.loads(packet_path.read_text(encoding='utf-8'))
            synthesis_id = str(payload.get('synthesis_id', packet_path.stem))
            reason = self._validate_packet(payload)
            if reason is not None:
                issues.append({'synthesis_id': synthesis_id, 'reason': reason})

        report = {
            'scene_id': scene_id,
            'total': len(packet_paths),
            'valid': len(packet_paths) - len(issues),
            'invalid': len(issues),
            'issues': issues,
        }
        output_path = output_dir / f'{scene_id}_synthesis_validation.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        report['output_path'] = str(output_path)
        return report

    def _validate_packet(self, payload: Dict[str, Any]) -> str | None:
        required_present = [
            'synthesis_id',
            'shot_id',
            'scene_id',
            'prompt',
            'camera_move',
            'timing_curve',
            'negative_prompt',
            'continuity_locks',
        ]
        for field in required_present:
            if field not in payload:
                return f'missing field: {field}'

        prompt = payload.get('prompt')
        if not isinstance(prompt, str) or not prompt.strip():
            return 'prompt is empty'

        negative_prompt = payload.get('negative_prompt')
        if not isinstance(negative_prompt, str) or not negative_prompt.strip():
            return 'negative_prompt is empty'

        continuity_locks = payload.get('continuity_locks')
        if not isinstance(continuity_locks, dict) or not continuity_locks:
            return 'continuity_locks is empty'

        for path_key in ('previous_frame', 'target_frame'):
            path_value = payload.get(path_key)
            if not path_value:
                return f'missing field: {path_key}'
            if not Path(str(path_value)).exists():
                return f'{path_key} does not exist: {path_value}'

        output_frame_path = payload.get('output_frame_path')
        if not output_frame_path:
            return 'missing field: output_frame_path'
        if not Path(str(output_frame_path)).parent.exists():
            return f'output_frame_path parent does not exist: {Path(str(output_frame_path)).parent}'

        temporal_position = payload.get('temporal_position')
        if not isinstance(temporal_position, (float, int)):
            return 'temporal_position must be numeric'
        if not 0.0 <= float(temporal_position) <= 1.0:
            return f'temporal_position out of range: {temporal_position}'

        bool_fields = [
            'preserve_identity',
            'preserve_environment',
            'preserve_lighting',
            'preserve_camera_axis',
        ]
        for field in bool_fields:
            if not isinstance(payload.get(field), bool):
                return f'{field} must be boolean'

        return None
