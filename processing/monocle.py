"""
processing/monocle.py — giph5lens v3
Medidas reais (paquímetro):
  Frame externo : 31.0 × 17.0 mm  →  366 × 201 px @ 300 DPI
  Display/janela: 27.0 × 14.0 mm  →  319 × 165 px @ 300 DPI
  Borda lateral : 2.0 mm cada lado →  24 px
  Borda vertical: 1.5 mm cada lado →  18 px
  Bleed         : 0.3 mm (rebaixo apertado)
  Grid A4       : 5 × 14 = 70 monóculos
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List
from PIL import Image, ImageDraw, ImageEnhance

MM_PER_INCH = 25.4

# ── Constantes físicas reais ──────────────────────────────────────────────────
OUTER_W_MM    = 31.0   # frame externo largura
OUTER_H_MM    = 17.0   # frame externo altura
DISPLAY_W_MM  = 27.0   # janela óptica largura  → 319 px
DISPLAY_H_MM  = 14.0   # janela óptica altura   → 165 px
BORDER_W_MM   = (OUTER_W_MM - DISPLAY_W_MM) / 2   # 2.0 mm cada lado
BORDER_H_MM   = (OUTER_H_MM - DISPLAY_H_MM) / 2   # 1.5 mm cada lado
BLEED_MM      = 0.3
RADIUS_MM     = 1.0
A4_W_MM       = 210.0
A4_H_MM       = 297.0

def mm2px(mm: float, dpi: int = 300) -> int:
    return round((mm / MM_PER_INCH) * dpi)


@dataclass
class MonocleConfig:
    dpi: int   = 300
    round_corners: bool = True
    enhance_transparency: bool = False
    export_format: str = "PNG"      # "PNG" ou "TIFF"
    fill_mode: str = "repeat"       # "repeat" | "exact"
    gap_mm: float  = 2.0
    margin_mm: float = 8.0
    draw_cut_lines: bool = True     # tracejado de corte entre monóculos
    polaroid_border: bool = True    # borda branca + linha preta estilo Polaroid

    # calculados
    outer_w_px:   int = field(init=False)
    outer_h_px:   int = field(init=False)
    display_w_px: int = field(init=False)
    display_h_px: int = field(init=False)
    border_w_px:  int = field(init=False)
    border_h_px:  int = field(init=False)
    radius_px:    int = field(init=False)
    cols: int = field(init=False)
    rows: int = field(init=False)
    total: int = field(init=False)

    def __post_init__(self):
        d = self.dpi
        self.outer_w_px   = mm2px(OUTER_W_MM,   d)   # 366
        self.outer_h_px   = mm2px(OUTER_H_MM,   d)   # 201
        self.display_w_px = mm2px(DISPLAY_W_MM, d)   # 319
        self.display_h_px = mm2px(DISPLAY_H_MM, d)   # 165
        self.border_w_px  = mm2px(BORDER_W_MM,  d)   # 24
        self.border_h_px  = mm2px(BORDER_H_MM,  d)   # 18
        self.radius_px    = mm2px(RADIUS_MM,     d)   # 12
        usable_w = A4_W_MM - 2 * self.margin_mm
        usable_h = A4_H_MM - 2 * self.margin_mm
        self.cols  = int((usable_w + self.gap_mm) / (OUTER_W_MM + self.gap_mm))  # 5
        self.rows  = int((usable_h + self.gap_mm) / (OUTER_H_MM + self.gap_mm))  # 14
        self.total = self.cols * self.rows  # 70

    def summary(self) -> dict:
        return {
            "outer_px":     f"{self.outer_w_px}×{self.outer_h_px}",
            "display_px":   f"{self.display_w_px}×{self.display_h_px}",
            "dpi":          self.dpi,
            "cols":         self.cols,
            "rows":         self.rows,
            "total_per_a4": self.total,
            "format":       self.export_format,
            "fill_mode":    self.fill_mode,
        }


# ── helpers de imagem ─────────────────────────────────────────────────────────

def _open_any(path: str) -> Image.Image:
    """Abre qualquer formato → RGB."""
    raw = Image.open(path)
    if raw.mode in ("P", "PA"):
        raw = raw.convert("RGBA")
    return raw.convert("RGB")

def _crop_risk(src_w, src_h, tgt_w, tgt_h) -> str:
    diff = abs((src_w/src_h) - (tgt_w/tgt_h)) / (tgt_w/tgt_h)
    return "high" if diff > 0.35 else ("medium" if diff > 0.15 else "low")

def _cover_crop(img: Image.Image, tw: int, th: int) -> Image.Image:
    sw, sh = img.size
    scale  = max(tw / sw, th / sh)
    scale  = min(scale, 1.5) if scale > 1.0 else scale
    rsmp   = Image.BICUBIC if scale > 1.0 else Image.LANCZOS
    nw, nh = math.ceil(sw * scale), math.ceil(sh * scale)
    img    = img.resize((nw, nh), rsmp)
    l, t   = (nw - tw) // 2, (nh - th) // 2
    return img.crop((l, t, l + tw, t + th))

def _enhance(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Color(img).enhance(1.20)
    img = ImageEnhance.Sharpness(img).enhance(1.10)
    return img

def _rgba_safe(img: Image.Image) -> Image.Image:
    """Garante RGB para salvar como JPEG."""
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img.convert("RGB"), mask=img.getchannel("A"))
        return bg
    return img.convert("RGB") if img.mode != "RGB" else img


# ── Borda Polaroid ────────────────────────────────────────────────────────────

def _make_tile_polaroid(photo: Image.Image, cfg: MonocleConfig) -> Image.Image:
    """
    Monta o tile completo do monóculo com borda estilo Polaroid:
    - fundo branco no frame externo (366×201 px)
    - foto cropada centralizada na janela (319×165 px)
    - linha preta fina (2px) ao redor da janela
    - cantos arredondados opcionais
    """
    ow, oh = cfg.outer_w_px, cfg.outer_h_px
    dw, dh = cfg.display_w_px, cfg.display_h_px
    bw, bh = cfg.border_w_px, cfg.border_h_px

    # Canvas branco
    frame = Image.new("RGB", (ow, oh), (255, 255, 255))

    # Foto na janela interna
    photo_cropped = _cover_crop(photo, dw, dh)
    frame.paste(photo_cropped, (bw, bh))

    # Borda preta ao redor da janela (2px, estilo Polaroid)
    draw = ImageDraw.Draw(frame)
    draw.rectangle(
        [(bw - 2, bh - 2), (bw + dw + 1, bh + dh + 1)],
        outline=(0, 0, 0), width=2
    )

    # Cantos arredondados no frame inteiro
    if cfg.round_corners:
        frame = frame.convert("RGBA")
        mask = Image.new("L", (ow, oh), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [(0, 0), (ow - 1, oh - 1)], radius=cfg.radius_px, fill=255
        )
        frame.putalpha(mask)

    return frame


# ── Processador principal ─────────────────────────────────────────────────────

class MonocleProcessor:

    def __init__(self, config: MonocleConfig):
        self.cfg = config

    def process_single(self, source_path: str, output_path: str) -> dict:
        cfg  = self.cfg
        src  = _open_any(source_path)
        risk = _crop_risk(src.width, src.height, cfg.display_w_px, cfg.display_h_px)

        if cfg.enhance_transparency:
            src = _enhance(src)

        tile = _make_tile_polaroid(src, cfg) if cfg.polaroid_border else _cover_crop(src, cfg.outer_w_px, cfg.outer_h_px)

        if cfg.export_format == "TIFF":
            _rgba_safe(tile).save(output_path, format="TIFF", dpi=(cfg.dpi, cfg.dpi), compression="tiff_lzw")
        else:
            tile.save(output_path, format="PNG", dpi=(cfg.dpi, cfg.dpi))

        return {**cfg.summary(), "source_size": f"{src.width}×{src.height}", "crop_loss_risk": risk}

    def process_a4_sheet(
        self,
        source_paths: List[str],   # aceita 1 ou N fotos
        output_tiff: str,
        output_preview: str | None = None,
    ) -> dict:
        cfg    = self.cfg
        a4_w   = mm2px(A4_W_MM, cfg.dpi)   # 2480
        a4_h   = mm2px(A4_H_MM, cfg.dpi)   # 3508
        gap_px = mm2px(cfg.gap_mm, cfg.dpi)
        ow, oh = cfg.outer_w_px, cfg.outer_h_px

        # Centraliza o grid na folha
        grid_w = cfg.cols * ow + (cfg.cols - 1) * gap_px
        grid_h = cfg.rows * oh + (cfg.rows - 1) * gap_px
        off_x  = (a4_w - grid_w) // 2
        off_y  = (a4_h - grid_h) // 2

        # Pré-processa cada foto uma vez
        tiles = []
        risks = []
        for p in source_paths:
            src = _open_any(p)
            if cfg.enhance_transparency:
                src = _enhance(src)
            risks.append(_crop_risk(src.width, src.height, cfg.display_w_px, cfg.display_h_px))
            t = _make_tile_polaroid(src, cfg) if cfg.polaroid_border else _cover_crop(src, ow, oh)
            tiles.append(t)

        n_photos   = len(tiles)
        n_cells    = cfg.cols * cfg.rows
        fill_repeat = cfg.fill_mode == "repeat"

        # Canvas A4 branco
        canvas = Image.new("RGBA", (a4_w, a4_h), (255, 255, 255, 255))

        cell_idx = 0
        for row in range(cfg.rows):
            for col in range(cfg.cols):
                if not fill_repeat and cell_idx >= n_photos:
                    break
                tile = tiles[cell_idx % n_photos]
                x = off_x + col * (ow + gap_px)
                y = off_y + row * (oh + gap_px)
                if tile.mode == "RGBA":
                    canvas.paste(tile, (x, y), mask=tile)
                else:
                    canvas.paste(tile.convert("RGBA"), (x, y))
                cell_idx += 1

        # Tracejado de corte
        if cfg.draw_cut_lines:
            self._draw_cut_lines(canvas, off_x, off_y, ow, oh, gap_px)

        final = _rgba_safe(canvas)
        final.save(output_tiff, format="TIFF", dpi=(cfg.dpi, cfg.dpi), compression="tiff_lzw")

        if output_preview:
            prev = final.copy()
            prev.thumbnail((900, 900), Image.LANCZOS)
            prev.save(output_preview, format="JPEG", quality=90)

        max_risk = "high" if "high" in risks else ("medium" if "medium" in risks else "low")
        used_cells = min(n_cells, n_photos) if not fill_repeat else n_cells
        return {
            **cfg.summary(),
            "a4_px":          f"{a4_w}×{a4_h}",
            "photos_uploaded": n_photos,
            "cells_used":      used_cells,
            "crop_loss_risk":  max_risk,
        }

    def _draw_cut_lines(self, canvas, off_x, off_y, ow, oh, gap_px):
        """Cruzetas nos cantos + linhas tracejadas no centro de cada gap."""
        cfg   = self.cfg
        draw  = ImageDraw.Draw(canvas)
        gray  = (160, 160, 160, 220)
        ext   = 8    # extensão da cruzeta além da borda
        dash  = 10   # px tracejado ligado
        space = 6    # px tracejado desligado

        grid_w = cfg.cols * ow + (cfg.cols - 1) * gap_px
        grid_h = cfg.rows * oh + (cfg.rows - 1) * gap_px

        def dashed_h(x0, x1, y):
            x = x0
            while x < x1:
                draw.line([(x, y), (min(x + dash, x1), y)], fill=gray, width=1)
                x += dash + space

        def dashed_v(x, y0, y1):
            y = y0
            while y < y1:
                draw.line([(x, y), (x, min(y + dash, y1))], fill=gray, width=1)
                y += dash + space

        # Linhas tracejadas verticais entre colunas
        for col in range(1, cfg.cols):
            x_cut = off_x + col * (ow + gap_px) - gap_px // 2
            dashed_v(x_cut, off_y - ext, off_y + grid_h + ext)

        # Linhas tracejadas horizontais entre linhas
        for row in range(1, cfg.rows):
            y_cut = off_y + row * (oh + gap_px) - gap_px // 2
            dashed_h(off_x - ext, off_x + grid_w + ext, y_cut)

        # Cruzetas nos cantos de cada tile
        for row in range(cfg.rows):
            for col in range(cfg.cols):
                x  = off_x + col * (ow + gap_px)
                y  = off_y + row * (oh + gap_px)
                for cx, cy in [(x, y), (x+ow, y), (x, y+oh), (x+ow, y+oh)]:
                    draw.line([(cx-ext, cy), (cx+ext, cy)], fill=gray, width=1)
                    draw.line([(cx, cy-ext), (cx, cy+ext)], fill=gray, width=1)
