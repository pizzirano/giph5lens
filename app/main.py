"""
Lenticular Microtube Creator — FastAPI Backend
Entrelaçamento vertical para microtubo 5×5 cm / 100 LPI / 300 DPI
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request
from pydantic import BaseModel

from processing.interlace import InterlaceProcessor, ProcessingConfig

app = FastAPI(title="Lenticular Microtube Creator", version="1.0.0")

# Paths
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = Path("/tmp/microtube/uploads")
OUTPUT_DIR = Path("/tmp/microtube/outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


class JobStatus(BaseModel):
    job_id: str
    status: str
    message: str
    output_file: str | None = None


# In-memory job store (use Redis for production)
jobs: dict[str, JobStatus] = {}


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/process", response_model=JobStatus)
async def process_frames(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    lpi: int = 100,
    dpi: int = 300,
    size_cm: float = 5.0,
):
    """Recebe 2–4 frames e inicia o processamento de entrelaçamento."""
    if not (2 <= len(files) <= 4):
        raise HTTPException(status_code=400, detail="Envie entre 2 e 4 frames.")

    job_id = str(uuid.uuid4())[:8]
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True)

    # Salva uploads
    frame_paths = []
    for i, f in enumerate(files):
        dest = job_dir / f"frame_{i:02d}{Path(f.filename).suffix.lower()}"
        with open(dest, "wb") as buf:
            shutil.copyfileobj(f.file, buf)
        frame_paths.append(str(dest))

    jobs[job_id] = JobStatus(job_id=job_id, status="queued", message="Na fila…")

    config = ProcessingConfig(lpi=lpi, dpi=dpi, size_cm=size_cm)
    background_tasks.add_task(_run_job, job_id, frame_paths, config)

    return jobs[job_id]


@app.get("/api/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return jobs[job_id]


@app.get("/api/download/{job_id}")
async def download(job_id: str):
    job = jobs.get(job_id)
    if not job or job.status != "done":
        raise HTTPException(status_code=404, detail="Arquivo ainda não pronto.")
    path = OUTPUT_DIR / f"{job_id}_microtube.tiff"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no disco.")
    return FileResponse(
        path=str(path),
        media_type="image/tiff",
        filename=f"microtube_{job_id}.tiff",
    )


@app.get("/api/preview/{job_id}")
async def preview(job_id: str):
    """Retorna JPEG de preview (baixa resolução) para exibir no browser."""
    job = jobs.get(job_id)
    if not job or job.status != "done":
        raise HTTPException(status_code=404, detail="Preview não disponível.")
    path = OUTPUT_DIR / f"{job_id}_preview.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Preview não encontrado.")
    return FileResponse(path=str(path), media_type="image/jpeg")


# ── background task ──────────────────────────────────────────────────────────

def _run_job(job_id: str, frame_paths: list[str], config: ProcessingConfig):
    try:
        jobs[job_id] = JobStatus(job_id=job_id, status="processing", message="Processando…")
        processor = InterlaceProcessor(config)
        output_tiff = OUTPUT_DIR / f"{job_id}_microtube.tiff"
        preview_jpg = OUTPUT_DIR / f"{job_id}_preview.jpg"
        processor.run(frame_paths, str(output_tiff), str(preview_jpg))
        jobs[job_id] = JobStatus(
            job_id=job_id,
            status="done",
            message="Pronto! Arquivo TIFF gerado.",
            output_file=str(output_tiff),
        )
    except Exception as exc:
        jobs[job_id] = JobStatus(
            job_id=job_id, status="error", message=f"Erro: {exc}"
        )