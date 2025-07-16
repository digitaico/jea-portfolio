import numpy as np
from scipy.signal import find_peaks
from typing import List, Dict, Any

from shared.models.domain import FramePose
from shared.utils.constants import MediaPipeLandmarks
from .base_calculator import BaseMetricsCalculator


class CadenceCalculator(BaseMetricsCalculator):
    """Calculator for running cadence (steps per minute)"""
    
    def calculate(self, pose_data: List[FramePose]) -> Dict[str, Any]:
        """Calculate cadence from foot movement patterns"""
        if len(pose_data) < 10:
            return {"cadence": 0.0, "step_count": 0}
        
        # Get timestamps
        timestamps = np.array([frame.timestamp for frame in pose_data])
        total_time = timestamps[-1] - timestamps[0]
        
        if total_time <= 0:
            return {"cadence": 0.0, "step_count": 0}
        
        # Get foot positions
        left_foot = self.get_landmark_positions(pose_data, MediaPipeLandmarks.LEFT_ANKLE.value)
        right_foot = self.get_landmark_positions(pose_data, MediaPipeLandmarks.RIGHT_ANKLE.value)
        
        # Calculate vertical movements (y-axis)
        left_y = self.smooth_signal(left_foot[:, 1])
        right_y = self.smooth_signal(right_foot[:, 1])
        
        # Find peaks (foot contacts) - lower y values indicate ground contact
        left_peaks, _ = find_peaks(-left_y, height=0.01, distance=5)
        right_peaks, _ = find_peaks(-right_y, height=0.01, distance=5)
        
        # Total steps
        total_steps = len(left_peaks) + len(right_peaks)
        
        # Calculate cadence (steps per minute)
        cadence = (total_steps / total_time) * 60 if total_time > 0 else 0.0
        
        return {
            "cadence": cadence,
            "step_count": total_steps,
            "left_steps": len(left_peaks),
            "right_steps": len(right_peaks)
        }