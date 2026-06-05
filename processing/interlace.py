"""
processing/interlace.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Algoritmo de entrelaçamento vertical lenticular para microtubo 5×5 cm.

Fórmula-base:
  • Pixels totais  = round(size_cm / 2.54 * dpi)   →  ~591 px para 5 cm @ 300 DPI
  • Tira por frame = total_px / (lpi * n_frames)    →  ~1.5 px  para 100 LPI, 4 frames
  • Ciclo completo = tira * n_frames pixels de largura

O array final é montado com NumPy (slice por coluna) e salvo como TIFF
com metadado de resolução (DPI) para impressão 1:1.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import numpy as np
from PIL import Image, ImageFilter


@dataclass
class ProcessingConfig:
    lpi: int = 100        # Linhas por polegada da folha lenticular
    dpi: int = 300        # Resolução de impressão
    size_cm: float = 5.0  # Tamanho do microtube (quadrado)
    sharpen: bool = True  # Aplicar leve sharpening no output
    # Calculados automaticamente
    total_px: int = field(init=False)
    strip_width_f: float = field(init=False)  # Largura de tira (float)

    def __post_init__(self):
        self.total_px = round(self.size_cm / 2.54 * self.dpi)
        # Será recalculado com n_frames real em InterlaceProcessor

    def recalc(self, n_frames: int) -> None:
        """Recalcula tira depois de conhecer quantos frames existem."""
        self.strip_width_f = self.total_px / (self.lpi * n_frames)


class InterlaceProcessor:
    """Lê N frames, redimensiona para total_px × total_px, entrelaça e salva."""

    def __init__(self, config: ProcessingConfig):
        self.cfg = config

    # ── public API ──────────────────────────────────────────────────────────

    def run(
        self,
        frame_paths: List[str],
        output_tiff: str,
        output_preview: str | None = None,
    ) -> None:
        n = len(frame_paths)
        if not (2 <= n <= 4):
            raise ValueError(f"Esperado 2–4 frames, recebido {n}.")

        self.cfg.recalc(n)
        frames = [self._load_and_normalize(p) for p in frame_paths]
        interlaced = self._interlace(frames)

        self._save_tiff(interlaced, output_tiff)
        if output_preview:
            self._save_preview(interlaced, output_preview)

    # ── private helpers ─────────────────────────────────────────────────────

    def _load_and_normalize(self, path: str) -> np.ndarray:
        """Abre imagem, converte para RGB e redimensiona para total_px²."""
        px = self.cfg.total_px
        img = Image.open(path).convert("RGB")
        img = img.resize((px, px), Image.LANCZOS)
        return np.asarray(img, dtype=np.uint8)

    def _interlace(self, frames: List[np.ndarray]) -> np.ndarray:
        """
        Monta a imagem entrelaçada pixel-a-pixel por coluna.

        Estratégia de distribuição sub-pixel (Bresenham-style):
          Como strip_width_f pode ser não inteiro (ex: 1.477 px),
          acumulamos o erro e alternamos entre floor/ceil para manter
          a largura total exata = total_px colunas.
        """
        n = len(frames)
        total_px = self.cfg.total_px
        strip_f = self.cfg.strip_width_f

        output = np.zeros((total_px, total_px, 3), dtype=np.uint8)

        col = 0
        acc = 0.0          # acumulador de erro sub-pixel
        frame_idx = 0

        while col < total_px:
            # Largura desta tira com distribuição de erro
            acc += strip_f
            strip_w = math.floor(acc)
            acc -= strip_w
            strip_w = max(1, min(strip_w, total_px - col))  # clamp

            end = min(col + strip_w, total_px)
            output[:, col:end, :] = frames[frame_idx % n][:, col:end, :]

            col = end
            frame_idx += 1

        return output

    def _save_tiff(self, arr: np.ndarray, path: str) -> None:
        """Salva TIFF com metadados de DPI para impressão 1:1."""
        img = Image.fromarray(arr, "RGB")
        if self.cfg.sharpen:
            img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=80, threshold=2))
        dpi = self.cfg.dpi
        img.save(
            path,
            format="TIFF",
            dpi=(dpi, dpi),
            compression="tiff_lzw",
        )

    def _save_preview(self, arr: np.ndarray, path: str) -> None:
        """Salva JPEG 600px para preview no browser."""
        img = Image.fromarray(arr, "RGB")
        img.thumbnail((600, 600), Image.LANCZOS)
        img.save(path, format="JPEG", quality=90)


# ── CLI standalone ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Uso: python interlace.py frame1.jpg frame2.jpg [frame3.jpg frame4.jpg] output.tiff")
        sys.exit(1)

    *inputs, out = sys.argv[1:]
    cfg = ProcessingConfig()
    proc = InterlaceProcessor(cfg)
    proc.run(inputs, out, out.replace(".tiff", "_preview.jpg"))
    print(f"✓ Salvo em {out}  |  total_px={cfg.total_px}  strip={cfg.strip_width_f:.4f}px")
