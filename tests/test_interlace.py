"""
tests/test_interlace.py
Testes para o algoritmo de entrelaçamento vertical.
Execute com: pytest -v
"""

import pytest
import numpy as np
from PIL import Image
import tempfile, os

from processing.interlace import InterlaceProcessor, ProcessingConfig


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_solid_frame(path: str, color: tuple, size: int = 200) -> str:
    """Cria um frame sólido de cor para teste."""
    img = Image.new("RGB", (size, size), color)
    img.save(path)
    return path


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestProcessingConfig:
    def test_total_px_5cm_300dpi(self):
        cfg = ProcessingConfig(dpi=300, size_cm=5.0)
        # 5 / 2.54 * 300 = 590.55... → 591
        assert cfg.total_px == 591

    def test_total_px_5cm_150dpi(self):
        cfg = ProcessingConfig(dpi=150, size_cm=5.0)
        assert cfg.total_px == round(5 / 2.54 * 150)

    def test_recalc_strip_4_frames(self):
        cfg = ProcessingConfig(lpi=100, dpi=300, size_cm=5.0)
        cfg.recalc(4)
        # 591 / (100 * 4) = 1.4775
        assert abs(cfg.strip_width_f - 591 / 400) < 1e-9

    def test_recalc_strip_2_frames(self):
        cfg = ProcessingConfig(lpi=100, dpi=300, size_cm=5.0)
        cfg.recalc(2)
        assert abs(cfg.strip_width_f - 591 / 200) < 1e-9


class TestInterlaceProcessor:

    def test_output_shape(self):
        cfg = ProcessingConfig(dpi=150, size_cm=5.0, sharpen=False)
        proc = InterlaceProcessor(cfg)

        with tempfile.TemporaryDirectory() as td:
            frames = [
                make_solid_frame(os.path.join(td, f"f{i}.png"), (i*60, i*30, 200-i*40))
                for i in range(4)
            ]
            out = os.path.join(td, "out.tiff")
            proc.run(frames, out)

            result = Image.open(out)
            expected = cfg.total_px
            assert result.size == (expected, expected)

    def test_output_has_dpi_metadata(self):
        cfg = ProcessingConfig(dpi=300, size_cm=5.0, sharpen=False)
        proc = InterlaceProcessor(cfg)

        with tempfile.TemporaryDirectory() as td:
            frames = [
                make_solid_frame(os.path.join(td, f"f{i}.png"), (i*60, 100, 200))
                for i in range(2)
            ]
            out = os.path.join(td, "out.tiff")
            proc.run(frames, out)

            img = Image.open(out)
            assert img.info.get("dpi") == (300, 300)

    def test_total_columns_match(self):
        """A imagem resultante deve ter exatamente total_px colunas."""
        cfg = ProcessingConfig(dpi=150, size_cm=5.0, sharpen=False)
        cfg.recalc(3)
        proc = InterlaceProcessor(cfg)

        with tempfile.TemporaryDirectory() as td:
            frames = [
                make_solid_frame(os.path.join(td, f"f{i}.png"), (i*80, i*50, 255-i*80))
                for i in range(3)
            ]
            out = os.path.join(td, "out.tiff")
            proc.run(frames, out)

            arr = np.asarray(Image.open(out))
            assert arr.shape[1] == cfg.total_px

    def test_interlacing_alternates_frames(self):
        """
        Com 2 frames de cores opostas (vermelho e azul), a imagem entrelaçada
        não deve ser inteiramente de uma cor só.
        """
        cfg = ProcessingConfig(dpi=150, size_cm=5.0, sharpen=False)
        proc = InterlaceProcessor(cfg)

        with tempfile.TemporaryDirectory() as td:
            f1 = make_solid_frame(os.path.join(td, "red.png"),  (255, 0, 0))
            f2 = make_solid_frame(os.path.join(td, "blue.png"), (0, 0, 255))
            out = os.path.join(td, "out.tiff")
            proc.run([f1, f2], out)

            arr = np.asarray(Image.open(out))
            # R e B devem ambos aparecer
            has_red  = np.any(arr[:, :, 0] > 200)
            has_blue = np.any(arr[:, :, 2] > 200)
            assert has_red and has_blue

    def test_preview_created(self):
        cfg = ProcessingConfig(dpi=150, size_cm=5.0, sharpen=False)
        proc = InterlaceProcessor(cfg)

        with tempfile.TemporaryDirectory() as td:
            frames = [
                make_solid_frame(os.path.join(td, f"f{i}.png"), (100*i, 50, 200))
                for i in range(2)
            ]
            out     = os.path.join(td, "out.tiff")
            preview = os.path.join(td, "preview.jpg")
            proc.run(frames, out, preview)

            assert os.path.exists(preview)
            p = Image.open(preview)
            assert p.size[0] <= 600 and p.size[1] <= 600

    def test_rejects_single_frame(self):
        cfg = ProcessingConfig()
        proc = InterlaceProcessor(cfg)
        with pytest.raises(ValueError, match="2–4"):
            proc.run(["frame.jpg"], "out.tiff")

    def test_rejects_five_frames(self):
        cfg = ProcessingConfig()
        proc = InterlaceProcessor(cfg)
        with pytest.raises(ValueError):
            proc.run(["f.jpg"]*5, "out.tiff")
