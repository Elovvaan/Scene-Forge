from pathlib import Path
import json
from typing import Dict, List

from SAIN_OMEGA_CINEMA_ENGINE.continuity.chain import ContinuityChain
from SAIN_OMEGA_CINEMA_ENGINE.engine.frame_generator import FrameGenerator
from SAIN_OMEGA_CINEMA_ENGINE.engine.motion_validator import MotionPlanValidator
from SAIN_OMEGA_CINEMA_ENGINE.engine.storyboard_extractor import StoryboardExtractor
from SAIN_OMEGA_CINEMA_ENGINE.engine.temporal_engine import TemporalInterpolationEngine
from SAIN_OMEGA_CINEMA_ENGINE.engine.shot_inheritance import ShotInheritanceEngine
from SAIN_OMEGA_CINEMA_ENGINE.engine.motion_quality import MotionQualityScorer
from SAIN_OMEGA_CINEMA_ENGINE.engine.frame_synthesis_bridge import FrameSynthesisBridge
from SAIN_OMEGA_CINEMA_ENGINE.engine.synthesis_validator import SynthesisPacketValidator
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
        self.temporal_engine = TemporalInterpolationEngine()
        self.inheritance_engine = ShotInheritanceEngine()
        self.motion_quality_scorer = MotionQualityScorer()
        self.frame_synthesis_bridge = FrameSynthesisBridge()
        self.synthesis_validator = SynthesisPacketValidator()

    def run(self, storyboard_sheet: Path, story_text: str = '') -> Dict[str, List[Path] | Path]:
        panels = self.extractor.extract_panels(storyboard_sheet)
        scene_id = storyboard_sheet.stem
        packets_dir = self.paths.packets / scene_id
        shot_packets = create_shot_packets(panels, packets_dir=packets_dir, scene_id=scene_id)

        all_candidates: List[Path] = []
        shot_payloads: List[Dict[str, object]] = []
        temporal_analysis: List[Dict[str, object]] = []
        synthesis_packets: List[Path] = []

        for packet_path in shot_packets:
            payload = json.loads(packet_path.read_text(encoding='utf-8'))
            shot_payloads.append(payload)
            shot_id = payload.get('shot_id', Path(payload['start_frame']).stem)
            emotion = payload.get('emotion', 'neutral')
            generated = self.generator.generate_candidates(Path(payload['start_frame']), count=1, shot_id=shot_id, emotion=emotion)
            target_generated = self.generator.generate_candidates(
                Path(payload['target_frame']),
                count=1,
                shot_id=f'{shot_id}_target',
                emotion=emotion,
            )

            motion_plan = self.generator.motion_plans.get(shot_id, {}).get('plan', {})
            temporal = self.temporal_engine.interpolate_shot(
                shot_id=shot_id,
                start_frame=Path(payload['start_frame']),
                generated_frames=(generated or []) + (target_generated or []),
                target_frame=Path(payload['target_frame']),
                motion_plan=motion_plan,
            )
            all_candidates.extend(temporal.sequence)
            temporal_analysis.append(temporal.analysis)

            shot_synthesis_dir = packets_dir / 'synthesis'
            shot_synthesis_packets = self.frame_synthesis_bridge.build_for_shot(
                shot_payload=payload,
                motion_plan_payload=self.generator.motion_plans.get(shot_id, {}),
                temporal_analysis=temporal.analysis,
                synthesis_dir=shot_synthesis_dir,
            )
            synthesis_packets.extend(shot_synthesis_packets)

        sequence = self.sequencer.sequence(all_candidates, self.paths.render_frames / 'sequence')
        states = [self.chain.analyze_frame(f, i) for i, f in enumerate(sequence, start=1)]
        self.chain.persist(states)

        video_path = self.assembler.assemble_mp4(sequence, self.paths.videos / f'{storyboard_sheet.stem}_cinema.mp4')
        motion_path = self.paths.continuity / f'{storyboard_sheet.stem}_motion_plans.json'
        motion_path.write_text(json.dumps(self.generator.motion_plans, indent=2), encoding='utf-8')


        inheritance_report = self.inheritance_engine.build_inheritance_chain(shot_payloads, self.generator.motion_plans)
        inheritance_path = self.paths.continuity / f'{storyboard_sheet.stem}_shot_inheritance.json'
        inheritance_path.write_text(json.dumps(inheritance_report, indent=2), encoding='utf-8')

        temporal_path = self.paths.continuity / f'{storyboard_sheet.stem}_temporal_analysis.json'
        temporal_path.write_text(json.dumps({'active': True, 'shots': temporal_analysis}, indent=2), encoding='utf-8')


        synthesis_manifest = self.frame_synthesis_bridge.write_manifest(
            scene_id=storyboard_sheet.stem,
            packet_paths=synthesis_packets,
            output_path=self.paths.continuity / f'{storyboard_sheet.stem}_synthesis_manifest.json',
        )

        synthesis_validation = self.synthesis_validator.validate_packets(
            scene_id=storyboard_sheet.stem,
            packet_paths=synthesis_packets,
            output_dir=self.paths.continuity,
        )

        motion_quality = self.motion_quality_scorer.score_scene(
            scene_id=storyboard_sheet.stem,
            shot_payloads=shot_payloads,
            motion_plans=self.generator.motion_plans,
            temporal_analysis=temporal_analysis,
            output_dir=self.paths.continuity,
        )

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
            'temporal_active': self.temporal_engine.active,
            'shot_inheritance_active': self.inheritance_engine.active,
            'shot_inheritance': inheritance_path,
            'temporal_analysis': temporal_path,
            'synthesis_packets': synthesis_packets,
            'synthesis_manifest': synthesis_manifest,
            'motion_quality_score': motion_quality.overall_score,
            'motion_quality': motion_quality.output_path,
            'synthesis_validation_report': synthesis_validation,
            'synthesis_validation': Path(synthesis_validation['output_path']),
        }
