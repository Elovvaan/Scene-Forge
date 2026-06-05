from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import Iterable, List, Sequence


SUPPORTED_IMAGES = {'.jpg', '.jpeg', '.png', '.webp'}
SUPPORTED_STORYBOARDS = SUPPORTED_IMAGES | {'.pdf'}


class StoryboardExtractor:
    """Accepts PDF, image sheets, or ordered image sequences and emits ordered panel PNGs."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def extract_panels(self, source: Path | Sequence[Path]) -> List[Path]:
        if isinstance(source, (list, tuple)):
            return self._copy_sequence([Path(p) for p in source])

        source = Path(source)
        if source.is_dir():
            images = sorted(p for p in source.iterdir() if p.suffix.lower() in SUPPORTED_IMAGES)
            if not images:
                raise ValueError('Storyboard folder does not contain supported images (.jpg, .jpeg, .png, .webp).')
            return self._copy_sequence(images)

        suffix = source.suffix.lower()
        if suffix == '.pdf':
            return self._extract_pdf(source)
        if suffix in SUPPORTED_IMAGES:
            return self._extract_image_sheet(source)
        raise ValueError(f'Unsupported storyboard format: {source.suffix}')

    def _copy_sequence(self, images: Iterable[Path]) -> List[Path]:
        images = list(images)
        shot_dir = self.output_dir / self._sequence_name(images)
        shot_dir.mkdir(parents=True, exist_ok=True)
        panels: List[Path] = []
        for idx, image in enumerate(images, start=1):
            out = shot_dir / f'panel_{idx:03d}.png'
            if image.suffix.lower() == '.png':
                shutil.copy2(image, out)
            else:
                try:
                    from PIL import Image
                except ImportError as exc:
                    raise RuntimeError('Image storyboard intake requires Pillow. Install requirements.txt.') from exc
                Image.open(image).convert('RGB').save(out)
            panels.append(out)
        return panels

    def _extract_pdf(self, pdf_path: Path) -> List[Path]:
        try:
            import fitz  # PyMuPDF
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError('PDF storyboard intake requires PyMuPDF and Pillow. Install requirements.txt.') from exc

        rendered: List[Path] = []
        temp_dir = self.output_dir / pdf_path.stem / '_pdf_pages'
        temp_dir.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(pdf_path)
        for page_index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            out = temp_dir / f'page_{page_index:03d}.png'
            Image.frombytes('RGB', [pix.width, pix.height], pix.samples).save(out)
            rendered.append(out)
        if not rendered:
            raise ValueError('PDF storyboard did not contain renderable pages.')
        if len(rendered) == 1:
            return self._extract_image_sheet(rendered[0], scene_name=pdf_path.stem)
        return self._copy_sequence(rendered)

    def _extract_image_sheet(self, sheet_path: Path, scene_name: str | None = None) -> List[Path]:
        try:
            from PIL import Image, ImageChops, ImageStat
        except ImportError as exc:
            raise RuntimeError('Image storyboard intake requires Pillow. Install requirements.txt.') from exc

        img = Image.open(sheet_path).convert('RGB')
        w, h = img.size
        cols, rows = self._guess_grid(w, h)
        panel_w = w // cols
        panel_h = h // rows

        shot_dir = self.output_dir / (scene_name or sheet_path.stem)
        shot_dir.mkdir(parents=True, exist_ok=True)

        panels: List[Path] = []
        idx = 1
        for r in range(rows):
            for c in range(cols):
                left = c * panel_w
                top = r * panel_h
                right = w if c == cols - 1 else (c + 1) * panel_w
                bottom = h if r == rows - 1 else (r + 1) * panel_h
                crop = img.crop((left, top, right, bottom))
                # Skip almost-empty cells from non-full grids.
                stat = ImageStat.Stat(ImageChops.invert(crop.convert('L')))
                if stat.mean[0] < 2:
                    continue
                panel_path = shot_dir / f'panel_{idx:03d}.png'
                crop.save(panel_path)
                panels.append(panel_path)
                idx += 1
        return panels

    def _guess_grid(self, width: int, height: int) -> tuple[int, int]:
        aspect = width / max(height, 1)
        if aspect >= 1.8:
            return 4, 2
        if aspect >= 1.2:
            return 3, 2
        if aspect >= 0.85:
            return 3, 3
        return 2, 4

    def _sequence_name(self, images: Sequence[Path]) -> str:
        if not images:
            return 'storyboard_sequence'
        parent = images[0].parent.name
        return parent if parent else images[0].stem
