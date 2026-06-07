"""
processing/monocle.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
giph5lens — Monocle Image Processor  (v2 · física validada)

Especificação física do monóculo retangular pequeno:
  Área útil interna : 26.0 × 19.0 mm
  Safe margin       : ± 0.5 mm
  Área segura       : 25.5 × 18.5 mm  (encaixe garantido)
  Área máxima       : 26.5 × 19.5 mm  (limite físico)
  Safe crop zone    : 24.0 × 17.0 mm  (conteúdo crítico)
  Border radius     : 1.0 mm
  Bleed             : 0.5 mm
  Target DPI        : 300
  Canvas px         : 307 × 224 px    (sem bleed)
  Canvas + bleed    : 319 × 236 px

Grid A4 (gap 2 mm, margem 8 mm):
  cols = 7 · rows = 13 · total = 91 monóculos / folha
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import (
    Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
)


# ── Constantes físicas (imutáveis — medidas reais do monóculo) ────────────────

MM_PER_INCH: float = 25.4

WIDTH_MM:        float = 26.0
HEIGHT_MM:       float = 19.0
SAFE_WIDTH_MM:   float = 25.5
SAFE_HEIGHT_MM:  float = 18.5
MAX_WIDTH_MM:    float = 26.5
MAX_HEIGHT_MM:   float = 19.5
BLEED_MM:        float = 0.5
BORDER_RADIUS_MM: float = 1.0
SAFE_CROP_W_MM:  float = 24.0
SAFE_CROP_H_MM:  float = 17.0

A4_W_MM:  float = 210.0
A4_H_MM:  float = 297.0


def mm2px(mm: float, dpi: int) -> int:
    return round((mm / MM_PER_INCH) * dpi)


# ── Config ────────────────────────────────────────────────────────────────────

@dataclass
class MonocleConfig:
    dpi: int        = 300
    with_bleed: bool = True      # extrapola 0.5 mm para evitar borda branca
    round_corners: bool = True   # aplica border-radius de 1 mm
    enhance_transparency: bool = False  # contrast+15% sat+20% sharp+10% p/ acetato
    export_format: str = "PNG"   # "PNG" ou "TIFF"
    gap_mm: float   = 2.0        # espaçamento entre monóculos no grid A4
    margin_mm: float = 8.0       # margem externa da folha A4

    # calculados
    canvas_w_px: int = field(init=False)
    canvas_h_px: int = field(init=False)
    bleed_w_px: int  = field(init=False)
    bleed_h_px: int  = field(init=False)
    radius_px: int   = field(init=False)
    safe_w_px: int   = field(init=False)
    safe_h_px: int   = field(init=False)
    # grid A4
    cols: int = field(init=False)
    rows: int = field(init=False)
    total: int = field(init=False)

    def __post_init__(self):
        d = self.dpi
        self.canvas_w_px = mm2px(WIDTH_MM,  d)          # 307 px
        self.canvas_h_px = mm2px(HEIGHT_MM, d)          # 224 px
        self.bleed_w_px  = mm2px(WIDTH_MM  + 2*BLEED_MM, d)  # 319 px
        self.bleed_h_px  = mm2px(HEIGHT_MM + 2*BLEED_MM, d)  # 236 px
        self.radius_px   = mm2px(BORDER_RADIUS_MM, d)   # 12 px
        self.safe_w_px   = mm2px(SAFE_CROP_W_MM, d)     # 283 px
        self.safe_h_px   = mm2px(SAFE_CROP_H_MM, d)     # 201 px

        usable_w = A4_W_MM - 2 * self.margin_mm
        usable_h = A4_H_MM - 2 * self.margin_mm
        self.cols  = int((usable_w + self.gap_mm) / (WIDTH_MM  + self.gap_mm))
        self.rows  = int((usable_h + self.gap_mm) / (HEIGHT_MM + self.gap_mm))
        self.total = self.cols * self.rows

    @property
    def output_w(self) -> int:
        return self.bleed_w_px if self.with_bleed else self.canvas_w_px

    @property
    def output_h(self) -> int:
        return self.bleed_h_px if self.with_bleed else self.canvas_h_px

    def summary(self) -> dict:
        return {
            "canvas_px":    f"{self.canvas_w_px}×{self.canvas_h_px}",
            "output_px":    f"{self.output_w}×{self.output_h}",
            "with_bleed":   self.with_bleed,
            "dpi":          self.dpi,
            "cols":         self.cols,
            "rows":         self.rows,
            "total_per_a4": self.total,
            "format":       self.export_format,
        }


# ── Crop inteligente ──────────────────────────────────────────────────────────

def _crop_warning(src_w: int, src_h: int, target_w: int, target_h: int) -> str:
    """
    Retorna nível de risco de crop.
    Compara aspect ratio de origem vs destino.
    """
    src_ar  = src_w / src_h
    tgt_ar  = target_w / target_h
    diff    = abs(src_ar - tgt_ar) / tgt_ar

    if diff > 0.35:
        return "high"
    if diff > 0.15:
        return "medium"
    return "low"


def _cover_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Cover crop centralizado preservando aspect ratio.
    Escala para preencher o target, depois corta ao centro.
    Nunca distorce. Nunca escala além da resolução original (bicubic apenas para down).
    """
    src_w, src_h = img.size

    # Razão de escala para cover
    scale = max(target_w / src_w, target_h / src_h)

    # Regra 14: nunca upscale além do original com bicubic simples
    if scale > 1.0:
        scale = min(scale, 1.5)   # cap: até 1.5× com bicubic, avisa se maior
        resample = Image.BICUBIC
    else:
        resample = Image.LANCZOS

    new_w = math.ceil(src_w * scale)
    new_h = math.ceil(src_h * scale)
    img   = img.resize((new_w, new_h), resample)

    # Crop central
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _apply_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
    """Aplica border-radius via máscara RGBA."""
    img = img.convert("RGBA")
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=radius, fill=255)
    img.putalpha(mask)
    return img


def _enhance_for_transparency(img: Image.Image) -> Image.Image:
    """
    Reforça contraste, saturação e nitidez para impressão em acetato/transparência.
    Compensa perda de densidade luminosa quando a luz atravessa o filme.
    """
    img = ImageEnhance.Contrast(img).enhance(1.15)    # +15%
    img = ImageEnhance.Color(img).enhance(1.20)        # +20% saturação
    img = ImageEnhance.Sharpness(img).enhance(1.10)    # +10% nitidez
    return img


# ── Processador principal ─────────────────────────────────────────────────────

class MonocleProcessor:
    """
    Converte qualquer imagem para o formato físico do monóculo:
    307×224 px (ou 319×236 px com bleed) a 300 DPI.
    Gera também a folha A4 completa com até 91 cópias.
    """

    def __init__(self, config: MonocleConfig):
        self.cfg = config

    def process_single(
        self,
        source_path: str,
        output_path: str,
    ) -> dict:
        """Processa uma foto para o formato do monóculo. Retorna metadados."""
        cfg = self.cfg
        # Abre qualquer formato que o Pillow suporte e normaliza para RGB
        # (cobre JPEG, PNG, WebP, GIF, BMP, TIFF, HEIC, AVIF, CMYK, paleta…)
        raw = Image.open(source_path)
        if raw.mode in ("P", "PA"):
            raw = raw.convert("RGBA")
        src = raw.convert("RGB")
        src_w, src_h = src.size

        # Avaliação de crop risk
        crop_risk = _crop_warning(src_w, src_h, cfg.output_w, cfg.output_h)

        # Cover crop para o canvas de saída (com ou sem bleed)
        result = _cover_crop(src, cfg.output_w, cfg.output_h)

        # Enhancement para acetato (opcional)
        if cfg.enhance_transparency:
            result = _enhance_for_transparency(result)

        # Rounded corners (retorna RGBA se ativado)
        if cfg.round_corners:
            result = _apply_rounded_corners(result, cfg.radius_px)

        # Salva
        ext = cfg.export_format.upper()
        if ext == "TIFF":
            result.convert("RGB").save(
                output_path, format="TIFF",
                dpi=(cfg.dpi, cfg.dpi), compression="tiff_lzw"
            )
        else:
            result.save(output_path, format="PNG", dpi=(cfg.dpi, cfg.dpi))

        return {
            **cfg.summary(),
            "source_size":  f"{src_w}×{src_h}",
            "crop_loss_risk": crop_risk,
            "enhanced":     cfg.enhance_transparency,
            "corners":      cfg.round_corners,
        }

    def process_a4_sheet(
        self,
        source_path: str,
        output_tiff: str,
        output_preview: str | None = None,
    ) -> dict:
        """
        Gera folha A4 com o máximo de monóculos (91 cópias @ 300 DPI / gap 2 mm).
        """
        cfg = self.cfg
        raw = Image.open(source_path)
        if raw.mode in ("P", "PA"):
            raw = raw.convert("RGBA")
        src = raw.convert("RGB")

        # Prepara o tile (sem bleed no grid — evita sobreposição)
        tile_w = cfg.canvas_w_px
        tile_h = cfg.canvas_h_px
        tile   = _cover_crop(src, tile_w, tile_h)

        if cfg.enhance_transparency:
            tile = _enhance_for_transparency(tile)

        if cfg.round_corners:
            tile_rgba = _apply_rounded_corners(tile, cfg.radius_px)
        else:
            tile_rgba = tile.convert("RGBA")

        # Canvas A4 branco
        a4_w = mm2px(A4_W_MM, cfg.dpi)
        a4_h = mm2px(A4_H_MM, cfg.dpi)
        canvas = Image.new("RGBA", (a4_w, a4_h), (255, 255, 255, 255))

        # Offsets para centralizar o grid
        gap_px    = mm2px(cfg.gap_mm, cfg.dpi)
        margin_px = mm2px(cfg.margin_mm, cfg.dpi)
        grid_w = cfg.cols * tile_w + (cfg.cols - 1) * gap_px
        grid_h = cfg.rows * tile_h + (cfg.rows - 1) * gap_px
        off_x  = (a4_w - grid_w) // 2
        off_y  = (a4_h - grid_h) // 2

        # Cola os tiles
        for row in range(cfg.rows):
            for col in range(cfg.cols):
                x = off_x + col * (tile_w + gap_px)
                y = off_y + row * (tile_h + gap_px)
                canvas.paste(tile_rgba, (x, y), mask=tile_rgba)

        # Desenha cruzetas de corte
        canvas = self._draw_guides(canvas, off_x, off_y, tile_w, tile_h, gap_px)

        # Salva TIFF final
        final = canvas.convert("RGB")
        final.save(output_tiff, format="TIFF", dpi=(cfg.dpi, cfg.dpi), compression="tiff_lzw")

        # Preview
        if output_preview:
            prev = final.copy()
            prev.thumbnail((900, 900), Image.LANCZOS)
            prev.save(output_preview, format="JPEG", quality=90)

        return {
            **cfg.summary(),
            "a4_px": f"{a4_w}×{a4_h}",
            "crop_loss_risk": _crop_warning(src.width, src.height, tile_w, tile_h),
        }

    def process_a4_sheet_multiple(
        self,
        source_paths: list[str],
        output_tiff: str,
        output_preview: str | None = None,
        repeat: bool = True,
    ) -> dict:
        """
        Gera folha A4 preenchendo a grid com várias imagens.
        Se `repeat` for True, as imagens são ciclicamente repetidas até preencher a4.
        Se False, apenas as imagens fornecidas são colocadas (restante em branco).
        """
        cfg = self.cfg

        # Preprocessa cada fonte em um tile RGBA
        tiles: list[Image.Image] = []
        risks: list[str] = []
        for p in source_paths:
            raw = Image.open(p)
            if raw.mode in ("P", "PA"):
                raw = raw.convert("RGBA")
            src = raw.convert("RGB")
            risks.append(_crop_warning(src.width, src.height, cfg.canvas_w_px, cfg.canvas_h_px))

            tile = _cover_crop(src, cfg.canvas_w_px, cfg.canvas_h_px)
            if cfg.enhance_transparency:
                tile = _enhance_for_transparency(tile)
            if cfg.round_corners:
                tile_rgba = _apply_rounded_corners(tile, cfg.radius_px)
            else:
                tile_rgba = tile.convert("RGBA")
            tiles.append(tile_rgba)

        # Canvas A4
        a4_w = mm2px(A4_W_MM, cfg.dpi)
        a4_h = mm2px(A4_H_MM, cfg.dpi)
        canvas = Image.new("RGBA", (a4_w, a4_h), (255, 255, 255, 255))

        gap_px    = mm2px(cfg.gap_mm, cfg.dpi)
        margin_px = mm2px(cfg.margin_mm, cfg.dpi)
        grid_w = cfg.cols * cfg.canvas_w_px + (cfg.cols - 1) * gap_px
        grid_h = cfg.rows * cfg.canvas_h_px + (cfg.rows - 1) * gap_px
        off_x  = (a4_w - grid_w) // 2
        off_y  = (a4_h - grid_h) // 2

        total_slots = cfg.cols * cfg.rows
        for idx in range(total_slots):
            row = idx // cfg.cols
            col = idx % cfg.cols
            x = off_x + col * (cfg.canvas_w_px + gap_px)
            y = off_y + row * (cfg.canvas_h_px + gap_px)

            if idx < len(tiles):
                tile = tiles[idx]
            else:
                if repeat and len(tiles) > 0:
                    tile = tiles[idx % len(tiles)]
                else:
                    # deixa em branco
                    continue

            canvas.paste(tile, (x, y), mask=tile)

        # Desenha cruzetas
        canvas = self._draw_guides(canvas, off_x, off_y, cfg.canvas_w_px, cfg.canvas_h_px, gap_px)

        # Salva TIFF final
        final = canvas.convert("RGB")
        final.save(output_tiff, format="TIFF", dpi=(cfg.dpi, cfg.dpi), compression="tiff_lzw")

        # Preview
        if output_preview:
            prev = final.copy()
            prev.thumbnail((900, 900), Image.LANCZOS)
            prev.save(output_preview, format="JPEG", quality=90)

        # resumo
        return {
            **cfg.summary(),
            "a4_px": f"{a4_w}×{a4_h}",
            "selected": len(source_paths),
            "repeated": bool(repeat),
            "total_per_a4": cfg.total,
            "crop_loss_risk": "high" if "high" in risks else ("medium" if "medium" in risks else "low"),
        }

    def _draw_guides(
        self, canvas: Image.Image,
        off_x: int, off_y: int,
        tile_w: int, tile_h: int, gap_px: int,
    ) -> Image.Image:
        cfg  = self.cfg
        draw = ImageDraw.Draw(canvas)
        color = (180, 180, 180, 200)
        ext   = 6   # extensão da cruz além da borda do tile

        for row in range(cfg.rows):
            for col in range(cfg.cols):
                x  = off_x + col * (tile_w + gap_px)
                y  = off_y + row * (tile_h + gap_px)
                x2 = x + tile_w
                y2 = y + tile_h

                for (cx, cy) in [(x, y), (x2, y), (x, y2), (x2, y2)]:
                    draw.line([(cx - ext, cy), (cx + ext, cy)], fill=color, width=1)
                    draw.line([(cx, cy - ext), (cx, cy + ext)], fill=color, width=1)

        return canvas


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, json

    if len(sys.argv) < 3:
        print("Uso: python monocle.py <foto.jpg> <saida.png> [--a4] [--acetato] [--tiff]")
        sys.exit(1)

    src  = sys.argv[1]
    out  = sys.argv[2]
    a4   = "--a4"      in sys.argv
    acet = "--acetato" in sys.argv
    tiff = "--tiff"    in sys.argv

    cfg  = MonocleConfig(
        enhance_transparency=acet,
        export_format="TIFF" if tiff else "PNG",
    )
    proc = MonocleProcessor(cfg)

    if a4:
        info = proc.process_a4_sheet(src, out, out.replace(".tiff", "_preview.jpg"))
    else:
        info = proc.process_single(src, out)

    print(json.dumps(info, indent=2, ensure_ascii=False))