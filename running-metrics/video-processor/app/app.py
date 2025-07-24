import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID

from shared.database.connection import get_async_session
from shared.database.repository import RunningSessionRepository, PoseDataRepository
from shared.models.domain import ProcessingStatus
from .services.video_service import VideoService
from .services.video_processor import VideoProcessor
from .services.pose_detector import PoseDetector
from shared.events.event_bus import EventBus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
video_service: VideoService = None
event_bus: EventBus | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Initialize services
    global video_service, event_bus
    event_bus = EventBus()
    await event_bus.start()
    
    pose_detector = PoseDetector()
    video_processor = VideoProcessor(pose_detector)
    
    # Note: In a real microservice, these would be injected
    video_service = VideoService(
        video_processor=video_processor,
        session_repository=None,  # Will be injected per request
        pose_repository=None,     # Will be injected per request
        event_publisher=event_bus.publish,  # type: ignore[arg-type]
    )
    
    yield
    
    # Cleanup
    pose_detector.close()
    video_processor.cleanup()
    if event_bus:
        await event_bus.stop()


app = FastAPI(
    title="Running Metrics - Video Processor",
    description="Video processing service for running analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "video-processor"}


@app.post("/process/{session_id}")
async def process_video(
    session_id: UUID,
    video_path: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """Process video for pose detection"""
    try:
        # Create repositories with current session
        session_repo = RunningSessionRepository(session)
        pose_repo = PoseDataRepository(session)
        
        # Update service with current repositories
        video_service.session_repository = session_repo
        video_service.pose_repository = pose_repo
        
        # Add background task
        background_tasks.add_task(
            video_service.process_video_async,
            session_id,
            video_path
        )
        
        return {"message": "Video processing started", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Error starting video processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/annotate/{session_id}")
async def create_annotated_video(
    session_id: UUID,
    input_path: str,
    output_path: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Create annotated video with pose landmarks"""
    try:
        # Create repositories
        session_repo = RunningSessionRepository(session)
        pose_repo = PoseDataRepository(session)
        
        # Update service
        video_service.session_repository = session_repo
        video_service.pose_repository = pose_repo
        
        # Create annotated video
        result_path = await video_service.create_annotated_video(
            session_id, input_path, output_path
        )
        
        return {"message": "Annotated video created", "output_path": result_path}
        
    except Exception as e:
        logger.error(f"Error creating annotated video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{session_id}")
async def get_processing_status(
    session_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get processing status for a session"""
    try:
        session_repo = RunningSessionRepository(session)
        session_data = await session_repo.get_by_id(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "status": session_data.status,
            "error_message": session_data.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)