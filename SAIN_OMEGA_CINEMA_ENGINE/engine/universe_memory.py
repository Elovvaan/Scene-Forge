from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_MEMORY: Dict[str, Any] = {
    'characters': [],
    'locations': [],
    'episode_notes': '',
    'visual_style': 'cinematic, grounded, director-first continuity',
    'camera_rules': 'preserve screen direction, lens language, lighting continuity, and spatial geography',
}


class UniverseMemory:
    """Flat JSON memory used by the desktop MVP; no graphs, vectors, or embeddings."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(DEFAULT_MEMORY.copy())

    def load(self) -> Dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, FileNotFoundError):
            data = DEFAULT_MEMORY.copy()
            self.save(data)
        for key, value in DEFAULT_MEMORY.items():
            data.setdefault(key, value)
        return data

    def save(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def prompt_context(self) -> str:
        memory = self.load()
        return '\n'.join(
            [
                f"Characters: {memory.get('characters', [])}",
                f"Locations: {memory.get('locations', [])}",
                f"Episode Notes: {memory.get('episode_notes', '')}",
                f"Visual Style: {memory.get('visual_style', '')}",
                f"Camera Rules: {memory.get('camera_rules', '')}",
            ]
        )
