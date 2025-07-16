import numpy as np
from typing import List, Dict, Any

from shared.models.domain import FramePose
from shared.utils.constants import MediaPipeLandmarks, RunningConstants
from .base_calculator import BaseMetricsCalculator


class SpeedCalculator(BaseMetricsCalculator):
    """Calculator for running speed"""
    
    def calculate(self, pose_data: List[FramePose]) -> Dict[str, Any]:
        """Calculate speed from stride analysis"""
        if len(pose_data) < 10:
            return {"speed": 0.0, "distance": 0.0}
        
        # Get hip center positions (average of left and right hip)
        left_hip = self.get_landmark_positions(pose_data, MediaPipeLandmarks.LEFT_HIP.value)
        right_hip = self.get_landmark_positions(pose_data, MediaPipeLandmarks.RIGHT_HIP.value)
        
        # Calculate hip center
        hip_center = (left_hip + right_hip) / 2
        
        # Smooth the trajectory
        hip_center_smooth = np.array([
            self.smooth_signal(hip_center[:, 0]),
            self.smooth_signal(hip_center[:, 1]),
            self.smooth_signal(hip_center[:, 2])
        ]).T
        
        # Calculate frame-to-frame displacement
        displacements = np.diff(hip_center_smooth, axis=0)
        
        # Calculate distances (focus on forward movement - x-axis)
        distances = np.sqrt(np.sum(displacements**2, axis=1))
        
        # Convert to real-world units using height reference
        # Assume the person's height in pixels corresponds to their actual height
        pixel_to_meter_ratio = self.height_m / np.mean([
            np.abs(left_hip[:, 1].max() - left_hip[:, 1].min()),
            np.abs(right_hip[:, 1].max() - right_hip[:, 1].min())
        ])
        
        real_distances = distances * pixel_to_meter_ratio
        
        # Calculate total distance
        total_distance = np.sum(real_distances)
        
        # Calculate time
        timestamps = np.array([frame.timestamp for frame in pose_data])
        total_time = timestamps[-1] - timestamps[0]
        
        # Calculate speed
        speed = total_distance / total_time if total_time > 0 else 0.0
        
        return {
            "speed": speed,
            "distance": total_distance,
            "average_frame_distance": np.mean(real_distances)
        }