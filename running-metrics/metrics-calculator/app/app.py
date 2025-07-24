import logging
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.connection import get_async_session
from shared.database.repository import (
    RunningSessionRepository,
    PoseDataRepository,
    RunningMetricsRepository,
)
from shared.database.models import RunningMetricsDB
from .services.metrics_service import MetricsService
from shared.events.event_bus import EventBus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service placeholder (repositories injected per request)
metrics_service: MetricsService | None = None
event_bus: EventBus | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create metrics_service once and reuse it across requests."""
    global metrics_service, event_bus
    # Initialize in-memory event bus
    event_bus = EventBus()
    await event_bus.start()
    metrics_service = MetricsService(
        session_repository=None,  # will be set per request
        pose_repository=None,
        metrics_repository=None,
        event_bus=event_bus,
    )
    yield
    # Shutdown
    if event_bus:
        await event_bus.stop()


app = FastAPI(
    title="Running Metrics - Metrics Calculator",
    description="Service that calculates advanced running metrics from pose data",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow CORS from anywhere (configurable)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "metrics-calculator"}


@app.post("/calculate/{session_id}")
async def calculate_metrics(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    """Kick off metrics calculation for a given running session."""
    try:
        # Wire repositories for this request
        session_repo = RunningSessionRepository(session)
        pose_repo = PoseDataRepository(session)
        metrics_repo = RunningMetricsRepository(session)

        # Ensure service is initialized
        if metrics_service is None:
            raise HTTPException(status_code=500, detail="Service not initialized")

        # Inject repositories for this request
        metrics_service.session_repository = session_repo
        metrics_service.pose_repository = pose_repo
        metrics_service.metrics_repository = metrics_repo

        background_tasks.add_task(metrics_service.compute_metrics_for_session, session_id)
        return {"message": "Metrics calculation started", "session_id": session_id}
    except Exception as e:
        logger.error(f"Failed to start metrics calculation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/{session_id}")
async def get_metrics(
    session_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Return stored metrics for a session, if present."""
    try:
        metrics_repo = RunningMetricsRepository(session)

        metrics_db: RunningMetricsDB | None = await metrics_repo.get_by_session_id(session_id)
        if not metrics_db:
            raise HTTPException(status_code=404, detail="Metrics not found")

        return {
            "session_id": session_id,
            "metrics": {
                "cadence": metrics_db.cadence,
                "speed": metrics_db.speed,
                "step_length": metrics_db.step_length,
                "stride_length": metrics_db.stride_length,
                "ground_contact_time": metrics_db.ground_contact_time,
                "flight_time": metrics_db.flight_time,
                "vertical_oscillation": metrics_db.vertical_oscillation,
                "forward_lean": metrics_db.forward_lean,
                "left_right_symmetry": metrics_db.left_right_symmetry,
                "center_of_gravity": metrics_db.center_of_gravity,
                "joint_angles": metrics_db.joint_angles,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002) 