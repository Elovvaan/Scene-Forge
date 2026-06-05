from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ShotMetadataPacket:
    shot_id: str
    scene_id: str
    duration_seconds: float
    fps: int
    storyboard_panel: Path
    start_frame: Path
    end_frame: Path
    shot_description: str
    camera_move: str
    emotion: str
    motion_intensity: float
    visual_tone: str
    continuity_id: str
    continuity_context: Path | None = None
    references: List[str] = field(default_factory=list)
    output_dir: Path = Path('')
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def target_frame(self) -> Path:
        return self.end_frame

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        for key in ('storyboard_panel', 'start_frame', 'end_frame', 'continuity_context', 'output_dir'):
            if payload.get(key) is not None:
                payload[key] = str(payload[key])
        payload['target_frame'] = str(self.end_frame)
        return payload

    def save_json(self, packets_dir: Path) -> Path:
        import json

        packets_dir.mkdir(parents=True, exist_ok=True)
        packet_path = packets_dir / f'{self.shot_id}.json'
        packet_path.write_text(json.dumps(self.to_dict(), indent=2), encoding='utf-8')
        return packet_path


def build_shot_packets(
    panels: List[Path],
    packets_dir: Path,
    scene_id: str,
    shots_dir: Path | None = None,
    fps: int = 8,
) -> List[ShotMetadataPacket]:
    """Build one director-visible shot for each storyboard panel."""
    packets: List[ShotMetadataPacket] = []
    shots_dir = shots_dir or (packets_dir / 'shots')
    for i, panel in enumerate(panels, start=1):
        shot_id = f'shot{i:03d}'
        shot_dir = shots_dir / shot_id
        start_frame = shot_dir / 'start_frame.png'
        end_frame = shot_dir / 'end_frame.png'
        previous_end = shots_dir / f'shot{i - 1:03d}' / 'end_frame.png' if i > 1 else None
        packets.append(
            ShotMetadataPacket(
                shot_id=shot_id,
                scene_id=scene_id,
                duration_seconds=3.0,
                fps=fps,
                storyboard_panel=panel,
                start_frame=start_frame,
                end_frame=end_frame,
                shot_description=f'Shot {i:03d}: cinematic interpretation of storyboard panel {i}.',
                camera_move='subtle cinematic move',
                emotion='story-driven',
                motion_intensity=0.35,
                visual_tone='cinematic',
                continuity_id=f'{scene_id}_{shot_id}',
                continuity_context=previous_end,
                references=[str(panel)],
                output_dir=shot_dir,
            )
        )
    return packets


def create_shot_packet_files(
    panels: List[Path],
    packets_dir: Path,
    scene_id: str,
    shots_dir: Path | None = None,
    fps: int = 8,
) -> List[Path]:
    packet_paths: List[Path] = []
    for packet in build_shot_packets(panels, packets_dir, scene_id, shots_dir=shots_dir, fps=fps):
        packet_paths.append(packet.save_json(packets_dir))
    return packet_paths


def create_shot_packets(
    panels: List[Path],
    packets_dir: Path,
    scene_id: str,
    shots_dir: Path | None = None,
    fps: int = 8,
) -> List[Path]:
    return create_shot_packet_files(panels, packets_dir, scene_id, shots_dir=shots_dir, fps=fps)
