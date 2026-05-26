from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ShotPacket:
    shot_id: str
    scene_id: str
    duration_seconds: float
    fps: int
    start_frame: Path
    target_frame: Path
    storyboard_panel: Path
    camera_move: str
    emotion: str
    motion_intensity: float
    visual_tone: str
    continuity_id: str
    references: List[str] = field(default_factory=list)
    output_dir: Path = Path('')
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        for key in ('start_frame', 'target_frame', 'storyboard_panel', 'output_dir'):
            payload[key] = str(payload[key])
        return payload

    def save_json(self, packets_dir: Path) -> Path:
        import json

        packets_dir.mkdir(parents=True, exist_ok=True)
        packet_path = packets_dir / f'{self.shot_id}.json'
        packet_path.write_text(json.dumps(self.to_dict(), indent=2), encoding='utf-8')
        return packet_path


def create_shot_packets(panels: List[Path], packets_dir: Path, scene_id: str, fps: int = 8) -> List[Path]:
    """Create sliding-window shot packets from extracted clean panel images."""
    packet_paths: List[Path] = []
    for i in range(len(panels) - 1):
        start_panel = panels[i]
        target_panel = panels[i + 1]
        shot_id = f'shot_{i + 1:03d}'
        continuity_id = f'{scene_id}_{shot_id}'
        packet = ShotPacket(
            shot_id=shot_id,
            scene_id=scene_id,
            duration_seconds=2.0,
            fps=fps,
            start_frame=start_panel,
            target_frame=target_panel,
            storyboard_panel=start_panel,
            camera_move='static',
            emotion='neutral',
            motion_intensity=0.35,
            visual_tone='cinematic',
            continuity_id=continuity_id,
            references=[str(start_panel), str(target_panel)],
            output_dir=packets_dir,
        )
        packet_paths.append(packet.save_json(packets_dir))
    return packet_paths
