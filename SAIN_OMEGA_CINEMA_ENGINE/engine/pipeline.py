from pathlib import Path
from typing import Dict, List

from SAIN_OMEGA_CINEMA_ENGINE.continuity.chain import ContinuityChain
from SAIN_OMEGA_CINEMA_ENGINE.engine.frame_generator import FrameGenerator
from SAIN_OMEGA_CINEMA_ENGINE.engine.storyboard_extractor import StoryboardExtractor
from SAIN_OMEGA_CINEMA_ENGINE.render.sequencer import FrameSequencer
from SAIN_OMEGA_CINEMA_ENGINE.render.video_assembler import VideoAssembler
from SAIN_OMEGA_CINEMA_ENGINE.storage.paths import SAINPaths


class SAINOmegaPipeline:
    def __init__(self, paths: SAINPaths):
        self.paths = paths
        self.extractor = StoryboardExtractor(paths.storyboard_refs)
        self.generator = FrameGenerator(paths.render_frames)
        self.sequencer = FrameSequencer()
        self.assembler = VideoAssembler()
        self.chain = ContinuityChain(paths.continuity / 'continuity_chain.json')

    def run(self, storyboard_sheet: Path, story_text: str = '') -> Dict[str, List[Path] | Path]:
        panels = self.extractor.extract_panels(storyboard_sheet)
        all_candidates: List[Path] = []
        for p in panels:
            all_candidates.extend(self.generator.generate_candidates(p, count=2))

        sequence = self.sequencer.sequence(all_candidates, self.paths.render_frames / 'sequence')
        states = [self.chain.analyze_frame(f, i) for i, f in enumerate(sequence, start=1)]
        self.chain.persist(states)

        video_path = self.assembler.assemble_mp4(sequence, self.paths.videos / f'{storyboard_sheet.stem}_cinema.mp4')
        return {
            'panels': panels,
            'candidates': all_candidates,
            'sequence': sequence,
            'video': video_path,
            'continuity': self.chain.path,
        }
