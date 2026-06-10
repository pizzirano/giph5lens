"""
keepgram v3 — 31×17 mm · 70 por A4 · multi-upload · borda Polaroid
"""
import uuid, shutil
from pathlib import Path
from typing import List
from PIL import Image as PILImage

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from pydantic import BaseModel

from processing.monocle import MonocleProcessor, MonocleConfig

app = FastAPI(title="keepgram v3", version="3.0.0")

BASE_DIR   = Path(__file__).parent.parent  # /app — templates/ e static/ estão aqui
UPLOAD_DIR = Path("/tmp/microtube/uploads")
OUTPUT_DIR = Path("/tmp/microtube/outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


class JobStatus(BaseModel):
    job_id: str
    status: str
    message: str
    info: dict | None = None


jobs: dict[str, JobStatus] = {}


# ── Rotas ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})


@app.post("/api/process", response_model=JobStatus)
async def process(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    mode: str               = Form("a4"),
    dpi: int                = Form(300),
    round_corners: bool     = Form(True),
    enhance_transparency: bool = Form(False),
    export_format: str      = Form("PNG"),
    fill_mode: str          = Form("repeat"),
    gap_mm: float           = Form(2.0),
    margin_mm: float        = Form(8.0),
    draw_cut_lines: bool    = Form(True),
    polaroid_border: bool   = Form(True),
):
    if not files or len(files) > 70:
        raise HTTPException(400, "Envie de 1 a 70 fotos.")

    job_id  = str(uuid.uuid4())[:8]
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True)

    saved_paths = []
    for i, f in enumerate(files):
        ext  = Path(f.filename or "img").suffix.lower() or ".jpg"
        dest = job_dir / f"source_{i:02d}{ext}"
        with open(dest, "wb") as buf:
            shutil.copyfileobj(f.file, buf)
        saved_paths.append(str(dest))

    cfg = MonocleConfig(
        dpi=dpi,
        round_corners=round_corners,
        enhance_transparency=enhance_transparency,
        export_format=export_format,
        fill_mode=fill_mode,
        gap_mm=gap_mm,
        margin_mm=margin_mm,
        draw_cut_lines=draw_cut_lines,
        polaroid_border=polaroid_border,
    )

    jobs[job_id] = JobStatus(job_id=job_id, status="queued", message="Na fila…")
    background_tasks.add_task(_run_job, job_id, saved_paths, mode, cfg)
    return jobs[job_id]


@app.get("/api/status/{job_id}", response_model=JobStatus)
async def status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job não encontrado.")
    return jobs[job_id]


@app.get("/api/status-html/{job_id}")
async def status_html(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job não encontrado.")

    job = jobs[job_id]

    if job.status == "done":
        info   = job.info or {}
        risk   = info.get("crop_loss_risk", "low")
        cells  = info.get("cells_used", "?")
        photos = info.get("photos_uploaded", "?")
        dpi    = info.get("dpi", "300")
        fmt    = info.get("format", "PNG")

        html = f"""
        <p class="sm ok">{job.message}</p>
        <script>
          (function() {{
            const el = document.querySelector('[x-data]');
            if (!el) return;
            const alpine = Alpine.$data(el);
            alpine.progressPercent = 100;
            alpine.showResult      = true;
            alpine.resultInfo      = {{
              cells:  '{cells}',
              photos: '{photos}',
              dpi:    '{dpi}',
              format: '{fmt}',
              risk:   '{risk}',
              job_id: '{job_id}'
            }};
            document.getElementById('step-result')
              ?.scrollIntoView({{ behavior: 'smooth' }});
          }})();
        </script>
        """
        return HTMLResponse(html, headers={"HX-Trigger": "jobDone"})

    elif job.status == "error":
        html = f"""
        <p class="sm err">{job.message}</p>
        <script>
          (function() {{
            const el = document.querySelector('[x-data]');
            if (!el) return;
            const alpine = Alpine.$data(el);
            alpine.progressPercent = 0;
          }})();
        </script>
        """
        return HTMLResponse(html, headers={"HX-Trigger": "jobError"})

    else:
        html = f"""
        <p class="sm">{job.message}</p>
        <script>
          (function() {{
            const el = document.querySelector('[x-data]');
            if (!el) return;
            const alpine = Alpine.$data(el);
            alpine.progressPercent = 65;
          }})();
        </script>
        """
        return HTMLResponse(html)


@app.get("/api/download/{job_id}")
async def download(job_id: str):
    job = jobs.get(job_id)
    if not job or job.status != "done":
        raise HTTPException(404, "Arquivo não pronto.")
    for ext in (".tiff", ".png"):
        p = OUTPUT_DIR / f"{job_id}_out{ext}"
        if p.exists():
            media = "image/tiff" if ext == ".tiff" else "image/png"
            return FileResponse(str(p), media_type=media, filename=f"keepgram_{job_id}{ext}")
    raise HTTPException(404, "Arquivo não encontrado.")


@app.get("/api/preview/{job_id}")
async def preview(job_id: str):
    p = OUTPUT_DIR / f"{job_id}_preview.jpg"
    if not p.exists():
        raise HTTPException(404, "Preview não disponível.")
    return FileResponse(str(p), media_type="image/jpeg")


@app.get("/api/layout-calc")
async def layout_calc(dpi: int = 300, gap_mm: float = 2.0, margin_mm: float = 8.0):
    cfg = MonocleConfig(dpi=dpi, gap_mm=gap_mm, margin_mm=margin_mm)
    return cfg.summary()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rgba_safe(img: PILImage.Image) -> PILImage.Image:
    if img.mode in ("RGBA", "LA"):
        bg = PILImage.new("RGB", img.size, (255, 255, 255))
        bg.paste(img.convert("RGB"), mask=img.getchannel("A"))
        return bg
    return img.convert("RGB") if img.mode != "RGB" else img


def _run_job(job_id: str, paths: List[str], mode: str, cfg: MonocleConfig):
    try:
        jobs[job_id] = JobStatus(job_id=job_id, status="processing", message="Processando…")
        proc = MonocleProcessor(cfg)
        ext  = ".tiff" if cfg.export_format == "TIFF" else ".png"
        out  = str(OUTPUT_DIR / f"{job_id}_out{ext}")
        prev = str(OUTPUT_DIR / f"{job_id}_preview.jpg")
        n    = len(paths)

        if mode == "a4":
            info  = proc.process_a4_sheet(paths, out, prev)
            cells = info["cells_used"]
            msg   = (f"✓ {cells} monóculos na folha A4 "
                     f"({cfg.cols}×{cfg.rows}) · {n} foto{'s' if n > 1 else ''} · 300 DPI")
        else:
            info = proc.process_single(paths[0], out)
            risk = info.get("crop_loss_risk", "low")
            msg  = f"✓ Monóculo {info['outer_px']}" + (f" · ⚠ crop {risk}" if risk == "high" else "")
            img_prev = _rgba_safe(PILImage.open(out))
            img_prev.thumbnail((700, 700))
            img_prev.save(prev, format="JPEG", quality=88)

        jobs[job_id] = JobStatus(job_id=job_id, status="done", message=msg, info=info)

    except Exception as exc:
        import traceback
        jobs[job_id] = JobStatus(
            job_id=job_id, status="error",
            message=f"Erro: {exc}",
            info={"traceback": traceback.format_exc()}
        )


# ── Static files — SEMPRE por último ─────────────────────────────────────────
# O mount precisa vir depois de todas as rotas para não interceptar requests
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")