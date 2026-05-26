from pathlib import Path
from typing import List

import numpy as np
from PIL import Image


class VideoAssembler:
    def assemble_mp4(self, frame_paths: List[Path], out_path: Path, fps: int = 8) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import imageio.v2 as imageio

            frames = [imageio.imread(p) for p in frame_paths]
            imageio.mimsave(out_path, frames, fps=fps)
            return out_path
        except Exception:
            import cv2

            first = np.array(Image.open(frame_paths[0]).convert('RGB'))
            h, w, _ = first.shape
            writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
            for p in frame_paths:
                arr = np.array(Image.open(p).convert('RGB'))
                writer.write(cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
            writer.release()
            return out_path
