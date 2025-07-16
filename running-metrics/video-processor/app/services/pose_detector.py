import cv2
import mediapipe as mp
import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging

from shared.models.domain import PoseLandmark, FramePose
from shared.utils.constants import MediaPipeLandmarks, RunningConstants

logger = logging.getLogger(__name__)


@dataclass
class PoseDetectionConfig:
    """Configuration for pose detection"""
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    model_complexity: int = 1
    smooth_landmarks: bool = True
    enable_segmentation: bool = False
    smooth_segmentation: bool = True


class PoseDetector:
    """MediaPipe pose detection service"""
    
    def __init__(self, config: PoseDetectionConfig = None):
        self.config = config or PoseDetectionConfig()
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=self.config.min_detection_confidence,
            min_tracking_confidence=self.config.min_tracking_confidence,
            model_complexity=self.config.model_complexity,
            smooth_landmarks=self.config.smooth_landmarks,
            enable_segmentation=self.config.enable_segmentation,
            smooth_segmentation=self.config.smooth_segmentation
        )
        
        self.landmark_names = [landmark.name for landmark in MediaPipeLandmarks]
    
    def detect_pose(self, frame: np.ndarray) -> Optional[List[PoseLandmark]]:
        """Detect pose landmarks in a single frame"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame
            results = self.pose.process(rgb_frame)
            
            if not results.pose_landmarks:
                return None
            
            # Extract landmarks
            landmarks = []
            for landmark in results.pose_landmarks.landmark:
                landmarks.append(PoseLandmark(
                    x=landmark.x,
                    y=landmark.y,
                    z=landmark.z,
                    visibility=landmark.visibility
                ))
            
            return landmarks
            
        except Exception as e:
            logger.error(f"Error detecting pose: {e}")
            return None
    
    def calculate_pose_confidence(self, landmarks: List[PoseLandmark]) -> float:
        """Calculate overall pose confidence score"""
        if not landmarks:
            return 0.0
        
        # Focus on key running landmarks
        key_landmarks = [
            MediaPipeLandmarks.LEFT_HIP.value,
            MediaPipeLandmarks.RIGHT_HIP.value,
            MediaPipeLandmarks.LEFT_KNEE.value,
            MediaPipeLandmarks.RIGHT_KNEE.value,
            MediaPipeLandmarks.LEFT_ANKLE.value,
            MediaPipeLandmarks.RIGHT_ANKLE.value,
            MediaPipeLandmarks.LEFT_SHOULDER.value,
            MediaPipeLandmarks.RIGHT_SHOULDER.value
        ]
        
        total_confidence = 0.0
        for idx in key_landmarks:
            if idx < len(landmarks):
                total_confidence += landmarks[idx].visibility
        
        return total_confidence / len(key_landmarks)
    
    def is_valid_pose(self, landmarks: List[PoseLandmark]) -> bool:
        """Check if pose is valid for running analysis"""
        if not landmarks:
            return False
        
        confidence = self.calculate_pose_confidence(landmarks)
        return confidence >= RunningConstants.MIN_CONFIDENCE_THRESHOLD
    
    def draw_landmarks(self, frame: np.ndarray, landmarks: List[PoseLandmark]) -> np.ndarray:
        """Draw pose landmarks on frame"""
        if not landmarks:
            return frame
        
        # Convert landmarks to MediaPipe format
        landmark_list = []
        for landmark in landmarks:
            landmark_list.append(
                self.mp_pose.PoseLandmark(
                    x=landmark.x,
                    y=landmark.y,
                    z=landmark.z,
                    visibility=landmark.visibility
                )
            )
        
        # Create pose landmarks object
        pose_landmarks = type('PoseLandmarks', (), {'landmark': landmark_list})()
        
        # Draw landmarks
        annotated_frame = frame.copy()
        self.mp_drawing.draw_landmarks(
            annotated_frame,
            pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )
        
        return annotated_frame
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'pose'):
            self.pose.close()