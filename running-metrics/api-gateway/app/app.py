import os
import shutil
import logging
from uuid import uuid4, UUID
from pathlib import Path
from typing import Annotated

import cv2
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.connection import get_async_session
from shared.database.repository import RunningSessionRepository
from shared.database.models import RunningSessionDB, ProcessingStatus
from shared.models.domain import Gender
from shared.models.domain import VideoMetadata

# Constants
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_SERVICE_URL = os.getenv("VIDEO_SERVICE_URL", "http://localhost:8001")
METRICS_SERVICE_URL = os.getenv("METRICS_SERVICE_URL", "http://localhost:8002")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-gateway")

app = FastAPI(title="Running Metrics API Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api-gateway"}


def _extract_video_metadata(path: Path) -> VideoMetadata:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError("Cannot open uploaded video")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frames / fps if fps else 0
    cap.release()
    return VideoMetadata(
        filename=path.name,
        file_size=path.stat().st_size,
        duration=duration,
        fps=fps,
        width=width,
        height=height,
        format=path.suffix.lower(),
    )


@app.post("/sessions", status_code=201)
async def create_session(
    video: Annotated[UploadFile, File(...)],
    gender: Annotated[str, Form(...)],
    height_cm: Annotated[int, Form(...)],
    age: Annotated[int, Form(...)],
    email: Annotated[str, Form(...)],
    db: AsyncSession = Depends(get_async_session),
):
    # Save video
    session_id = uuid4()
    dest_path = UPLOAD_DIR / f"{session_id}_{video.filename}"
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    # Extract metadata
    try:
        metadata = _extract_video_metadata(dest_path)
    except Exception as e:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))

    # Persist session
    repo = RunningSessionRepository(db)
    session_db = RunningSessionDB(
        id=session_id,
        video_filename=metadata.filename,
        video_file_size=metadata.file_size,
        video_duration=metadata.duration,
        video_fps=metadata.fps,
        video_width=metadata.width,
        video_height=metadata.height,
        video_format=metadata.format,
        runner_gender=Gender(gender),
        runner_height_cm=height_cm,
        runner_age=age,
        runner_email=email,
        status=ProcessingStatus.PENDING,
    )
    await repo.create(session_db)

    # Call video-processing microservice
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{VIDEO_SERVICE_URL}/process/{session_id}",
                json={"video_path": str(dest_path)},
                timeout=60,
            )
        except Exception as e:
            logger.error(f"Failed to dispatch to video service: {e}")
            raise HTTPException(status_code=502, detail="Video service unavailable")

    return {"session_id": session_id}


@app.get("/sessions/{session_id}/status")
async def get_status(session_id: UUID, db: AsyncSession = Depends(get_async_session)):
    repo = RunningSessionRepository(db)
    session_db = await repo.get_by_id(session_id)
    if not session_db:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "status": session_db.status}


@app.get("/sessions/{session_id}/metrics")
async def get_metrics(session_id: UUID):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{METRICS_SERVICE_URL}/metrics/{session_id}", timeout=30)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json() 