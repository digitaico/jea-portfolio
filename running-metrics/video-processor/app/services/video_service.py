import asyncio
import os
from typing import List, Optional, Callable
from uuid import UUID
import logging

from shared.models.domain import RunningSession, FramePose, ProcessingStatus
from shared.models.events import VideoUploadedEvent, PoseDetectionCompletedEvent, ProcessingFailedEvent
from shared.database.repository import RunningSessionRepository, PoseDataRepository
from shared.database.models import RunningSessionDB, PoseDataDB
from .video_processor import VideoProcessor
from .pose_detector import PoseDetector

logger = logging.getLogger(__name__)


class VideoService:
    """Service for coordinating video processing operations"""
    
    def __init__(
        self,
        video_processor: VideoProcessor,
        session_repository: RunningSessionRepository,
        pose_repository: PoseDataRepository,
        event_publisher: Optional[Callable] = None
    ):
        self.video_processor = video_processor
        self.session_repository = session_repository
        self.pose_repository = pose_repository
        self.event_publisher = event_publisher
    
    async def process_video_async(self, session_id: UUID, video_path: str) -> bool:
        """Process video asynchronously"""
        try:
            # Get session from database
            session = await self.session_repository.get_by_id(session_id)
            if not session:
                raise ValueError(f"Session not found: {session_id}")
            
            # Update status to processing
            session.status = ProcessingStatus.PROCESSING
            await self.session_repository.update(session)
            
            # Process video and collect pose data
            pose_data_list = []
            
            def progress_callback(progress: float, message: str):
                logger.info(f"Session {session_id}: {progress:.1f}% - {message}")
            
            # Process video frames
            for frame_pose in self.video_processor.process_video(video_path, progress_callback):
                pose_data_list.append(frame_pose)
            
            # Save pose data to database
            await self._save_pose_data(session_id, pose_data_list)
            
            # Update session status
            session.status = ProcessingStatus.COMPLETED
            await self.session_repository.update(session)
            
            # Publish event
            if self.event_publisher:
                await self.event_publisher(PoseDetectionCompletedEvent(
                    session_id=session_id,
                    data={"frames_processed": len(pose_data_list)}
                ))
            
            logger.info(f"Video processing completed for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing video for session {session_id}: {e}")
            
            # Update session with error
            try:
                session = await self.session_repository.get_by_id(session_id)
                if session:
                    session.status = ProcessingStatus.FAILED
                    session.error_message = str(e)
                    await self.session_repository.update(session)
            except Exception as db_error:
                logger.error(f"Error updating session status: {db_error}")
            
            # Publish failure event
            if self.event_publisher:
                await self.event_publisher(ProcessingFailedEvent(
                    session_id=session_id,
                    error_message=str(e),
                    data={}
                ))
            
            return False
    
    async def _save_pose_data(self, session_id: UUID, pose_data_list: List[FramePose]):
        """Save pose data to database"""
        try:
            for frame_pose in pose_data_list:
                # Convert landmarks to JSON format
                landmarks_json = [
                    {
                        "x": landmark.x,
                        "y": landmark.y,
                        "z": landmark.z,
                        "visibility": landmark.visibility
                    }
                    for landmark in frame_pose.landmarks
                ]
                
                pose_data_db = PoseDataDB(
                    session_id=session_id,
                    frame_number=frame_pose.frame_number,
                    timestamp=frame_pose.timestamp,
                    landmarks=landmarks_json,
                    confidence=frame_pose.confidence
                )
                
                await self.pose_repository.create(pose_data_db)
                
        except Exception as e:
            logger.error(f"Error saving pose data: {e}")
            raise
    
    async def create_annotated_video(self, session_id: UUID, input_video_path: str, output_path: str) -> str:
        """Create annotated video with pose landmarks"""
        try:
            # Get pose data from database
            pose_data_db = await self.pose_repository.get_by_session_id(session_id)
            
            # Convert to domain objects
            pose_data = []
            for pose_db in pose_data_db:
                landmarks = [
                    PoseLandmark(
                        x=landmark["x"],
                        y=landmark["y"],
                        z=landmark["z"],
                        visibility=landmark["visibility"]
                    )
                    for landmark in pose_db.landmarks
                ]
                
                frame_pose = FramePose(
                    frame_number=pose_db.frame_number,
                    timestamp=pose_db.timestamp,
                    landmarks=landmarks,
                    confidence=pose_db.confidence
                )
                pose_data.append(frame_pose)
            
            # Create annotated video
            return self.video_processor.create_annotated_video(
                input_video_path, pose_data, output_path
            )
            
        except Exception as e:
            logger.error(f"Error creating annotated video: {e}")
            raise