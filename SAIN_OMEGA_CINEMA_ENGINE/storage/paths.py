from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SAINPaths:
    root: Path

    @property
    def ui(self) -> Path:
        return self.root / 'ui'

    @property
    def engine(self) -> Path:
        return self.root / 'engine'

    @property
    def render(self) -> Path:
        return self.root / 'render'

    @property
    def packets(self) -> Path:
        return self.root / 'packets'

    @property
    def continuity(self) -> Path:
        return self.root / 'continuity'

    @property
    def references(self) -> Path:
        return self.root / 'references'

    @property
    def outputs(self) -> Path:
        return self.root / 'outputs'

    @property
    def storage(self) -> Path:
        return self.root / 'storage'

    @property
    def project(self) -> Path:
        return self.root / 'project'

    @property
    def project_shots(self) -> Path:
        return self.project / 'shots'

    @property
    def universe_memory(self) -> Path:
        return self.project / 'universe_memory.json'

    @property
    def storyboard_refs(self) -> Path:
        return self.references / 'storyboard'

    @property
    def continuity_refs(self) -> Path:
        return self.references / 'continuity'

    @property
    def character_refs(self) -> Path:
        return self.references / 'character'

    @property
    def environment_refs(self) -> Path:
        return self.references / 'environment'

    @property
    def render_frames(self) -> Path:
        return self.outputs / 'frames'

    @property
    def videos(self) -> Path:
        return self.outputs / 'videos'

    def bootstrap(self) -> None:
        for p in [
            self.storyboard_refs,
            self.continuity_refs,
            self.character_refs,
            self.environment_refs,
            self.render_frames,
            self.videos,
            self.packets,
            self.continuity,
            self.project,
            self.project_shots,
        ]:
            p.mkdir(parents=True, exist_ok=True)
