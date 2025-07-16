import numpy as np
from scipy.signal import find_peaks
from typing import List, Dict, Any

from shared.models.domain import FramePose
from shared.utils.constants import MediaPipeLandmarks
from .base_calculator import BaseMetricsCalculator


class TimingCalculator(BaseMetricsCalculator):
    """Calculator for ground contact time and flight time"""
    
    def calculate(self, pose_data: List[FramePose]) -> Dict[str, Any]:
        """Calculate ground contact time and flight time"""
        if len(pose_data) < 20:
            return {
                "ground_contact_time": 0.0,
                "flight_time": 0.0,
                "contact_flight_ratio": 0.0
            }
        
        # Get timestamps and foot positions
        timestamps = np.array([frame.timestamp for frame in pose_data])
        left_foot = self.get_landmark_positions(pose_data, MediaPipeLandmarks.LEFT_ANKLE.value)
        right_foot = self.get_landmark_positions(pose_data, MediaPipeLandmarks.RIGHT_