from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List


class VideoAssembler:
    def assemble_clip(self, start_frame: Path, end_frame: Path, out_path: Path, duration_seconds: float = 3.0, fps: int = 8) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        frames = self._interpolate_frames(start_frame, end_frame, max(2, int(duration_seconds * fps)))
        return self.assemble_mp4(frames, out_path, fps=fps)

    def assemble_mp4(self, frame_paths: List[Path], out_path: Path, fps: int = 8) -> Path:
        if not frame_paths:
            raise ValueError('Cannot assemble an MP4 without frames.')
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import imageio.v2 as imageio

            frames = [imageio.imread(p) for p in frame_paths]
            imageio.mimsave(out_path, frames, fps=fps)
            return out_path
        except ImportError:
            try:
                import cv2
                import numpy as np
                from PIL import Image
            except ImportError as cv_error:
                raise RuntimeError('MP4 export requires imageio or opencv-python plus Pillow. Install requirements.txt.') from cv_error

            first = np.array(Image.open(frame_paths[0]).convert('RGB'))
            h, w, _ = first.shape
            writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
            for p in frame_paths:
                arr = np.array(Image.open(p).convert('RGB').resize((w, h)))
                writer.write(cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
            writer.release()
            return out_path
        except Exception:
            raise

    def concatenate_clips(self, clip_paths: List[Path], out_path: Path) -> Path:
        if not clip_paths:
            raise ValueError('Cannot export film without generated clips.')
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if len(clip_paths) == 1:
            shutil.copy2(clip_paths[0], out_path)
            return out_path
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg:
            list_file = out_path.parent / 'clip_list.txt'
            list_file.write_text(''.join(f"file '{clip.resolve()}'\n" for clip in clip_paths), encoding='utf-8')
            subprocess.run(
                [ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', str(list_file), '-c', 'copy', str(out_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return out_path
        # Dependency-light fallback: rebuild from available clip start/end frames stored beside each clip.
        try:
            import imageio.v2 as imageio
        except ImportError as exc:
            raise RuntimeError('Concatenating multiple clips requires ffmpeg or imageio. Install requirements.txt.') from exc
        frames = []
        for clip in clip_paths:
            frames.extend(imageio.mimread(clip))
        imageio.mimsave(out_path, frames, fps=8)
        return out_path

    def _interpolate_frames(self, start_frame: Path, end_frame: Path, frame_count: int) -> List[Path]:
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError('Clip generation requires Pillow. Install requirements.txt.') from exc

        work_dir = start_frame.parent / '_clip_frames'
        work_dir.mkdir(parents=True, exist_ok=True)
        start = Image.open(start_frame).convert('RGB').resize((1280, 720))
        end = Image.open(end_frame).convert('RGB').resize((1280, 720))
        frames: List[Path] = []
        for idx in range(frame_count):
            alpha = idx / max(frame_count - 1, 1)
            frame = Image.blend(start, end, alpha)
            out = work_dir / f'frame_{idx + 1:04d}.png'
            frame.save(out)
            frames.append(out)
        return frames
