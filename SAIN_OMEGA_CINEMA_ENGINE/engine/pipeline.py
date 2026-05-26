from pathlib import Path
import json
from typing import Dict, List

from SAIN_OMEGA_CINEMA_ENGINE.continuity.chain import ContinuityChain
from SAIN_OMEGA_CINEMA_ENGINE.engine.frame_generator import FrameGenerator
from SAIN_OMEGA_CINEMA_ENGINE.engine.motion_validator import MotionPlanValidator
from SAIN_OMEGA_CINEMA_ENGINE.engine.storyboard_extractor import StoryboardExtractor
from SAIN_OMEGA_CINEMA_ENGINE.packets.shot_packet import create_shot_packets
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
        self.motion_validator = MotionPlanValidator()

    def run(self, storyboard_sheet: Path, story_text: str = '') -> Dict[str, List[Path] | Path]:
        panels = self.extractor.extract_panels(storyboard_sheet)
        scene_id = storyboard_sheet.stem
        packets_dir = self.paths.packets / scene_id
        shot_packets = create_shot_packets(panels, packets_dir=packets_dir, scene_id=scene_id)

        all_candidates: List[Path] = []
        for packet_path in shot_packets:
            payload = json.loads(packet_path.read_text(encoding='utf-8'))
            shot_id = payload.get('shot_id', Path(payload['start_frame']).stem)
            emotion = payload.get('emotion', 'neutral')
            all_candidates.extend(self.generator.generate_candidates(Path(payload['start_frame']), count=1, shot_id=shot_id, emotion=emotion))
            all_candidates.extend(
                self.generator.generate_candidates(
                    Path(payload['target_frame']),
                    count=1,
                    shot_id=f'{shot_id}_target',
                    emotion=emotion,
                )
            )

        sequence = self.sequencer.sequence(all_candidates, self.paths.render_frames / 'sequence')
        states = [self.chain.analyze_frame(f, i) for i, f in enumerate(sequence, start=1)]
        self.chain.persist(states)

        video_path = self.assembler.assemble_mp4(sequence, self.paths.videos / f'{storyboard_sheet.stem}_cinema.mp4')
        motion_path = self.paths.continuity / f'{storyboard_sheet.stem}_motion_plans.json'
        motion_path.write_text(json.dumps(self.generator.motion_plans, indent=2), encoding='utf-8')

        validation_report = self.motion_validator.validate_all(self.generator.motion_plans)
        validation_path = self.paths.continuity / f'{storyboard_sheet.stem}_motion_validation.json'
        validation_path.write_text(json.dumps(validation_report, indent=2), encoding='utf-8')
        return {
            'panels': panels,
            'shot_packets': shot_packets,
            'candidates': all_candidates,
            'sequence': sequence,
            'video': video_path,
            'continuity': self.chain.path,
            'motion_plans': motion_path,
            'motion_validation': validation_path,
            'motion_validation_report': validation_report,
        }
