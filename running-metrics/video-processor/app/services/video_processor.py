import cv2
import os
import tempfile
from typing import List, Optional, Generator, Tuple
from pathlib import Path
import logging

from shared.models.domain import VideoMetadata, FramePose, PoseLandmark
from shared.utils.constants import RunningConstants
from .pose_detector import PoseDetector, PoseDetectionConfig

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Main video processing service"""
    
    def __init__(self, pose_detector: PoseDetector = None):
        self.pose_detector = pose_detector or PoseDetector()
        self.temp_dir = tempfile.mkdtemp()
    
    def validate_video(self, video_path: str) -> Tuple[bool, str, Optional[VideoMetadata]]:
        """Validate video file and extract metadata"""
        try:
            if not os.path.exists(video_path):
                return False, "Video file not found", None
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False, "Cannot open video file", None
            
            # Extract metadata
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            # Validate video properties
            if fps < RunningConstants.MIN_VIDEO_FPS:
                return False, f"Video FPS too low: {fps}, minimum required: {RunningConstants.MIN_VIDEO_FPS}", None
            
            if duration < RunningConstants.MIN_VIDEO_DURATION:
                return False, f"Video too short: {duration}s, minimum required: {RunningConstants.MIN_VIDEO_DURATION}s", None
            
            if duration > RunningConstants.MAX_VIDEO_DURATION:
                return False, f"Video too long: {duration}s, maximum allowed: {RunningConstants.MAX_VIDEO_DURATION}s", None
            
            file_size = os.path.getsize(video_path)
            if file_size > RunningConstants.MAX_VIDEO_SIZE:
                return False, f"Video file too large: {file_size} bytes, maximum allowed: {RunningConstants.MAX_VIDEO_SIZE} bytes", None
            
            # Create metadata object
            metadata = VideoMetadata(
                filename=os.path.basename(video_path),
                file_size=file_size,
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                format=os.path.splitext(video_path)[1].lower()
            )
            
            return True, "Video validation successful", metadata
            
        except Exception as e:
            logger.error(f"Error validating video: {e}")
            return False, f"Error validating video: {str(e)}", None
    
    def process_video(self, video_path: str, progress_callback=None) -> Generator[FramePose, None, None]:
        """Process video and yield pose data for each frame"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Cannot open video file")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            frame_number = 0
            processed_frames = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Calculate timestamp
                timestamp = frame_number / fps
                
                # Detect pose
                landmarks = self.pose_detector.detect_pose(frame)
                
                if landmarks and self.pose_detector.is_valid_pose(landmarks):
                    confidence = self.pose_detector.calculate_pose_confidence(landmarks)
                    
                    frame_pose = FramePose(
                        frame_number=frame_number,
                        timestamp=timestamp,
                        landmarks=landmarks,
                        confidence=confidence
                    )
                    
                    yield frame_pose
                    processed_frames += 1
                
                frame_number += 1
                
                # Progress callback
                if progress_callback:
                    progress = (frame_number / frame_count) * 100
                    progress_callback(progress, f"Processing frame {frame_number}/{frame_count}")
            
            cap.release()
            logger.info(f"Processed {processed_frames} valid frames out of {frame_number} total frames")
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            raise
    
    def create_annotated_video(self, video_path: str, pose_data: List[FramePose], output_path: str) -> str:
        """Create video with pose landmarks overlaid"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Cannot open input video")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Create pose data lookup
            pose_lookup = {pose.frame_number: pose for pose in pose_data}
            
            frame_number = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Add pose landmarks if available
                if frame_number in pose_lookup:
                    pose = pose_lookup[frame_number]
                    frame = self.pose_detector.draw_landmarks(frame, pose.landmarks)
                
                out.write(frame)
                frame_number += 1
            
            cap.release()
            out.release()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating annotated video: {e}")
            raise
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Error cleaning up temporary files: {e}")
