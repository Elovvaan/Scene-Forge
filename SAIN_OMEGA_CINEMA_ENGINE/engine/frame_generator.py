from pathlib import Path
from typing import List

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw


class FrameGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def generate_candidates(self, panel_path: Path, count: int = 3) -> List[Path]:
        img = Image.open(panel_path).convert('RGB')
        shot_name = panel_path.stem
        target_dir = self.output_dir / panel_path.parent.name / shot_name
        target_dir.mkdir(parents=True, exist_ok=True)

        variants = [
            self._cinematic_grade(img),
            self._contrast_push(img),
            self._dramatic_vignette(img),
        ]

        results: List[Path] = []
        for i, variant in enumerate(variants[:count], start=1):
            out_path = target_dir / f'candidate_{i:02d}.png'
            variant.save(out_path)
            results.append(out_path)
        return results

    def _cinematic_grade(self, img: Image.Image) -> Image.Image:
        c = ImageEnhance.Color(img).enhance(0.85)
        b = ImageEnhance.Brightness(c).enhance(0.95)
        return ImageEnhance.Contrast(b).enhance(1.25)

    def _contrast_push(self, img: Image.Image) -> Image.Image:
        sharp = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=2))
        return ImageEnhance.Contrast(sharp).enhance(1.4)

    def _dramatic_vignette(self, img: Image.Image) -> Image.Image:
        gray = ImageOps.grayscale(img)
        tinted = ImageOps.colorize(gray, black='#101320', white='#d6d2ca')
        overlay = Image.new('RGBA', tinted.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        w, h = tinted.size
        for i in range(20):
            alpha = int(6 + i * 2.5)
            draw.rectangle([i, i, w - i, h - i], outline=(0, 0, 0, alpha))
        return Image.alpha_composite(tinted.convert('RGBA'), overlay).convert('RGB')
