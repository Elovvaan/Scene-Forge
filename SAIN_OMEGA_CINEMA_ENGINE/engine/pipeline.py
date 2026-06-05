from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence

from SAIN_OMEGA_CINEMA_ENGINE.engine.frame_generator import FrameGenerator
from SAIN_OMEGA_CINEMA_ENGINE.engine.storyboard_extractor import StoryboardExtractor
from SAIN_OMEGA_CINEMA_ENGINE.engine.universe_memory import UniverseMemory
from SAIN_OMEGA_CINEMA_ENGINE.packets.shot_packet import create_shot_packets
from SAIN_OMEGA_CINEMA_ENGINE.render.video_assembler import VideoAssembler
from SAIN_OMEGA_CINEMA_ENGINE.render.video_provider import LocalPreviewVideoProvider, VideoProvider
from SAIN_OMEGA_CINEMA_ENGINE.storage.paths import SAINPaths


class SAINOmegaPipeline:
    """Director-first desktop MVP pipeline: storyboard in, MP4 film out."""

    def __init__(self, paths: SAINPaths, video_provider: VideoProvider | None = None):
        self.paths = paths
        self.extractor = StoryboardExtractor(paths.storyboard_refs)
        self.generator = FrameGenerator(paths.project_shots)
        self.assembler = VideoAssembler()
        self.memory = UniverseMemory(paths.universe_memory)
        self.video_provider = video_provider or LocalPreviewVideoProvider(self.assembler)
        self.panels: List[Path] = []
        self.shot_packets: List[Path] = []
        self.shot_payloads: List[Dict[str, object]] = []
        self.generated_clips: List[Path] = []
        self.scene_id = 'omega_project'

    def intake_storyboard(self, storyboard: Path | Sequence[Path]) -> Dict[str, object]:
        self.panels = self.extractor.extract_panels(storyboard)
        first = self.panels[0] if self.panels else Path('storyboard')
        self.scene_id = first.parent.name
        packets_dir = self.paths.packets / self.scene_id
        self.shot_packets = create_shot_packets(
            self.panels,
            packets_dir=packets_dir,
            scene_id=self.scene_id,
            shots_dir=self.paths.project_shots,
        )
        self.shot_payloads = [json.loads(packet.read_text(encoding='utf-8')) for packet in self.shot_packets]
        return {'panels': self.panels, 'shot_packets': self.shot_packets, 'shots': self.shot_payloads}

    def generate_frames(self, shot_index: int | None = None) -> Dict[str, object]:
        payloads = self._selected_payloads(shot_index)
        generated: List[Dict[str, str]] = []
        for payload in payloads:
            previous_end = Path(str(payload['continuity_context'])) if payload.get('continuity_context') else None
            prompt_context = self._build_prompt_context(payload, previous_end)
            frames = self.generator.generate_start_end_frames(
                storyboard_panel=Path(str(payload['storyboard_panel'])),
                shot_dir=Path(str(payload['output_dir'])),
                shot_id=str(payload['shot_id']),
                prompt_context=prompt_context,
                previous_end_frame=previous_end,
            )
            payload['start_frame'] = str(frames['start_frame'])
            payload['end_frame'] = str(frames['end_frame'])
            generated.append({k: str(v) for k, v in frames.items()})
        self._persist_manifest()
        return {'generated_frames': generated, 'shots': self.shot_payloads}

    def send_to_video(self, shot_index: int | None = None) -> Dict[str, object]:
        payloads = self._selected_payloads(shot_index)
        clips: List[Path] = []
        for payload in payloads:
            start = Path(str(payload['start_frame']))
            end = Path(str(payload['end_frame']))
            if not start.exists() or not end.exists():
                self.generate_frames(self.shot_payloads.index(payload))
            clip = self.video_provider.generate_video(start, end, payload)
            payload['clip'] = str(clip)
            clips.append(clip)
            if clip not in self.generated_clips:
                self.generated_clips.append(clip)
        self._persist_manifest()
        return {'clips': clips, 'shots': self.shot_payloads}

    def export_film(self) -> Path:
        clips = [Path(str(payload['clip'])) for payload in self.shot_payloads if payload.get('clip')]
        if len(clips) < len(self.shot_payloads):
            self.send_to_video()
            clips = [Path(str(payload['clip'])) for payload in self.shot_payloads if payload.get('clip')]
        final_path = self.paths.project / 'Final_Film.mp4'
        result = self.assembler.concatenate_clips(clips, final_path)
        self._persist_manifest(final_path=result)
        return result

    def run(self, storyboard_sheet: Path | Sequence[Path], story_text: str = '') -> Dict[str, object]:
        intake = self.intake_storyboard(storyboard_sheet)
        frames = self.generate_frames()
        clips = self.send_to_video()
        video_path = self.export_film()
        return {
            'panels': intake['panels'],
            'shot_packets': intake['shot_packets'],
            'shots': self.shot_payloads,
            'candidates': [Path(item['start_frame']) for item in frames['generated_frames']],
            'sequence': [Path(str(payload['end_frame'])) for payload in self.shot_payloads],
            'clips': clips['clips'],
            'video': video_path,
            'continuity': self.paths.universe_memory,
        }

    def continue_workflow(self) -> str:
        if not self.shot_payloads:
            return 'Upload a storyboard first.'
        missing_frames = [p for p in self.shot_payloads if not Path(str(p['start_frame'])).exists() or not Path(str(p['end_frame'])).exists()]
        if missing_frames:
            self.generate_frames()
            return 'Generated missing start and end frames.'
        missing_clips = [p for p in self.shot_payloads if not p.get('clip')]
        if missing_clips:
            self.send_to_video()
            return 'Sent shots to video provider.'
        self.export_film()
        return 'Exported Final_Film.mp4.'

    def _selected_payloads(self, shot_index: int | None) -> List[Dict[str, object]]:
        if shot_index is None:
            return self.shot_payloads
        if shot_index < 0 or shot_index >= len(self.shot_payloads):
            raise IndexError('Selected shot is out of range.')
        return [self.shot_payloads[shot_index]]

    def _build_prompt_context(self, payload: Dict[str, object], previous_end: Path | None) -> str:
        continuity = f'Previous shot end frame: {previous_end}' if previous_end and previous_end.exists() else 'First shot: establish visual language.'
        return '\n'.join(
            [
                str(payload.get('shot_description', '')),
                continuity,
                self.memory.prompt_context(),
            ]
        )

    def _persist_manifest(self, final_path: Path | None = None) -> Path:
        manifest = {
            'scene_id': self.scene_id,
            'project_dir': str(self.paths.project),
            'universe_memory': str(self.paths.universe_memory),
            'shots': self.shot_payloads,
            'final_film': str(final_path) if final_path else None,
        }
        out = self.paths.project / 'omega_project_manifest.json'
        out.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        return out
