from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np
from scipy.signal import savgol_filter

from shared.models.domain import FramePose, PoseLandmark, RunnerProfile
from shared.utils.constants import MediaPipeLandmarks


class BaseMetricsCalculator(ABC):
    """Base class for metrics calculators"""
    
    def __init__(self, runner_profile: RunnerProfile):
        self.runner_profile = runner_profile
        self.height_m = runner_profile.height_cm / 100.0
    
    @abstractmethod
    def calculate(self, pose_data: List[FramePose]) -> Dict[str, Any]:
        """Calculate specific metrics from pose data"""
        pass
    
    def smooth_signal(self, signal: np.ndarray, window_length: int = 5) -> np.ndarray:
        """Apply smoothing to signal data"""
        if len(signal) < window_length:
            return signal
        
        # Ensure window length is odd
        if window_length % 2 == 0:
            window_length += 1
        
        try:
            return savgol_filter(signal, window_length, 3, mode='nearest')
        except:
            return signal
    
    def get_landmark_positions(self, pose_data: List[FramePose], landmark_idx: int) -> np.ndarray:
        """Extract position data for a specific landmark"""
        positions = []
        for frame in pose_data:
            if landmark_idx < len(frame.landmarks):
                landmark = frame.landmarks[landmark_idx]
                positions.append([landmark.x, landmark.y, landmark.z])
            else:
                # Handle missing landmarks
                positions.append([0.0, 0.0, 0.0])
        
        return np.array(positions)
    
    def calculate_distance(self, point1: np.ndarray, point2: np.ndarray) -> float:
        """Calculate Euclidean distance between two points"""
        return np.sqrt(np.sum((point1 - point2) ** 2))
    
    def calculate_angle(self, point1: np.ndarray, point2: np.ndarray, point3: np.ndarray) -> float:
        """Calculate angle between three points (point2 is the vertex)"""
        vector1 = point1 - point2
        vector2 = point3 - point2
        
        # Calculate angle using dot product
        cos_angle = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Ensure value is in valid range
        
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg