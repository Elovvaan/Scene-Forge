from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


@dataclass
class ImageSynthesisPacket:
    synthesis_id: str
    shot_id: str
    scene_id: str
    previous_frame: Path
    target_frame: Path
    temporal_position: float
    camera_move: str
    motion_intensity: float
    timing_curve: str
    emotion_transition: str
    continuity_locks: Dict[str, Any]
    preserve_identity: bool
    preserve_environment: bool
    preserve_lighting: bool
    preserve_camera_axis: bool
    prompt: str
    negative_prompt: str
    output_frame_path: Path
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        for key in ('previous_frame', 'target_frame', 'output_frame_path'):
            payload[key] = str(payload[key])
        return payload

    def save_json(self, packets_dir: Path) -> Path:
        import json

        packets_dir.mkdir(parents=True, exist_ok=True)
        packet_path = packets_dir / f'{self.synthesis_id}.json'
        packet_path.write_text(json.dumps(self.to_dict(), indent=2), encoding='utf-8')
        return packet_path
