"""
giph5lens — Print Spooler para Monóculo Fotográfico
FastAPI + Uvicorn  ·  v2  ·  26×19 mm · 307×224 px · 300 DPI
"""

import uuid, shutil
from pathlib import Path
from PIL import Image as PILImage

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.requests import Request
from pydantic import BaseModel

from processing.monocle import MonocleProcessor, MonocleConfig

app = FastAPI(title="giph5lens — Monocle Print Spooler", version="2.0.0")

BASE_DIR   = Path(__file__).parent
UPLOAD_DIR = Path("/tmp/microtube/uploads")
OUTPUT_DIR = Path("/tmp/microtube/outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Formatos aceitos pelo Pillow — qualquer coisa que o Pillow abrir funciona
ACCEPTED_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "image/bmp", "image/tiff", "image/heic", "image/heif",
    "image/avif", "application/octet-stream",  # fallback para uploads sem mime
}


class JobStatus(BaseModel):
    job_id: str
    status: str
    message: str
    info: dict | None = None


jobs: dict[str, JobStatus] = {}


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/process", response_model=JobStatus)
async def process(
    background_tasks: BackgroundTasks,
    file: list[UploadFile] = File(...),
    mode: str              = Form("a4"),
    dpi: int               = Form(300),
    with_bleed: bool       = Form(True),
    round_corners: bool    = Form(True),
    enhance_transparency: bool = Form(False),
    export_format: str     = Form("PNG"),
    gap_mm: float          = Form(2.0),
    margin_mm: float       = Form(8.0),
    repeat: str            = Form("repeat"),
):
    job_id  = str(uuid.uuid4())[:8]
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True)

    # Salva todos os arquivos enviados
    sources: list[str] = []
    for idx, f in enumerate(file):
        raw_ext = Path(f.filename or f"upload{idx}").suffix.lower()
        ext  = raw_ext if raw_ext else ".jpg"
        dest = job_dir / f"source{idx}{ext}"
        with open(dest, "wb") as buf:
            shutil.copyfileobj(f.file, buf)
        sources.append(str(dest))

    cfg = MonocleConfig(
        dpi=dpi,
        with_bleed=with_bleed,
        round_corners=round_corners,
        enhance_transparency=enhance_transparency,
        export_format=export_format,
        gap_mm=gap_mm,
        margin_mm=margin_mm,
    )

    jobs[job_id] = JobStatus(job_id=job_id, status="queued", message="Na fila…")
    background_tasks.add_task(_run_job, job_id, sources if len(sources) > 1 else sources[0], mode, cfg, repeat)
    return jobs[job_id]


@app.get("/api/status/{job_id}", response_model=JobStatus)
async def status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job não encontrado.")
    return jobs[job_id]


@app.get("/api/download/{job_id}")
async def download(job_id: str):
    job = jobs.get(job_id)
    if not job or job.status != "done":
        raise HTTPException(404, "Arquivo ainda não pronto.")
    for ext in (".tiff", ".png"):
        path = OUTPUT_DIR / f"{job_id}_out{ext}"
        if path.exists():
            media = "image/tiff" if ext == ".tiff" else "image/png"
            return FileResponse(str(path), media_type=media, filename=f"giph5lens_{job_id}{ext}")
    raise HTTPException(404, "Arquivo não encontrado.")


@app.get("/api/preview/{job_id}")
async def preview(job_id: str):
    job = jobs.get(job_id)
    if not job or job.status != "done":
        raise HTTPException(404, "Preview não disponível.")
    path = OUTPUT_DIR / f"{job_id}_preview.jpg"
    if not path.exists():
        raise HTTPException(404, "Preview não encontrado.")
    return FileResponse(str(path), media_type="image/jpeg")


@app.get("/api/preview-print/{job_id}")
async def preview_print(job_id: str):
    # Página simples para imprimir o preview como PDF (window.print())
    if job_id not in jobs or jobs[job_id].status != 'done':
        raise HTTPException(404, "Preview não disponível para impressão.")
    html = (
        "<!doctype html>"
        "<html>"
        "<head><meta charset=\"utf-8\"><title>Preview · giph5lens</title></head>"
        "<body style=\"margin:0;padding:0;display:flex;align-items:center;justify-content:center;background:#fff\">"
        "<img src=\"/api/preview/" + job_id + "\" style=\"max-width:100%;height:auto;\"/>"
        "<script>window.onload = function() { setTimeout(function(){ window.print(); }, 300); };</script>"
        "</body>"
        "</html>"
    )
    return HTMLResponse(html)


@app.get("/api/layout-calc")
async def layout_calc(dpi: int = 300, gap_mm: float = 2.0, margin_mm: float = 8.0):
    cfg = MonocleConfig(dpi=dpi, gap_mm=gap_mm, margin_mm=margin_mm)
    return cfg.summary()


# ── helpers ───────────────────────────────────────────────────────────────────

def _rgba_to_jpeg_safe(img: PILImage.Image) -> PILImage.Image:
    """Converte qualquer modo para RGB com fundo branco — seguro para JPEG."""
    if img.mode in ("RGBA", "LA"):
        bg = PILImage.new("RGB", img.size, (255, 255, 255))
        alpha = img.getchannel("A")
        bg.paste(img.convert("RGB"), mask=alpha)
        return bg
    if img.mode == "P":
        return img.convert("RGB")
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def _save_preview(img: PILImage.Image, path: str, max_size: int = 700) -> None:
    """Salva JPEG de preview — garante RGB independente do modo de entrada."""
    img = img.copy()
    img.thumbnail((max_size, max_size), PILImage.LANCZOS)
    img = _rgba_to_jpeg_safe(img)
    img.save(path, format="JPEG", quality=88)


# ── background task ───────────────────────────────────────────────────────────

def _run_job(job_id: str, source, mode: str, cfg: MonocleConfig, repeat: str = "repeat"):
    try:
        jobs[job_id] = JobStatus(job_id=job_id, status="processing", message="Processando…")
        proc = MonocleProcessor(cfg)
        ext  = ".tiff" if cfg.export_format == "TIFF" else ".png"
        out  = str(OUTPUT_DIR / f"{job_id}_out{ext}")
        prev = str(OUTPUT_DIR / f"{job_id}_preview.jpg")

        if mode == "a4":
            # source may be a single path or a list of paths
            if isinstance(source, list):
                info = proc.process_a4_sheet_multiple(source, out, prev, repeat=(repeat == 'repeat'))
            else:
                info = proc.process_a4_sheet(source, out, prev)
            msg  = (f"✓ {info['total_per_a4']} monóculos "
                    f"({info['cols']}×{info['rows']}) · A4 · {cfg.dpi} DPI")
        else:
            info = proc.process_single(source, out)
            risk = info.get("crop_loss_risk", "low")
            msg  = (f"✓ Monóculo {info['output_px']} px"
                    + (f" · ⚠️ crop_loss_risk={risk}" if risk == "high" else ""))
            # preview do monóculo único — abre o arquivo gerado e converte safe
            _save_preview(PILImage.open(out), prev)

        jobs[job_id] = JobStatus(job_id=job_id, status="done", message=msg, info=info)

    except Exception as exc:
        import traceback
        jobs[job_id] = JobStatus(
            job_id=job_id, status="error",
            message=f"Erro: {exc}",
            info={"traceback": traceback.format_exc()}
        )