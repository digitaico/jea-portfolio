import numpy as np
from scipy.signal import find_peaks
from typing import List, Dict, Any

from shared.models.domain import FramePose
from shared.utils.constants import MediaPipeLandmarks, RunningConstants
from .base_calculator import BaseMetricsCalculator


class StrideCalculator(BaseMetricsCalculator):
    """Calculator for stride and step length"""
    
    def calculate(self, pose_data: List[FramePose]) -> Dict[str, Any]:
        """Calculate stride and step length from foot positions"""
        if len(pose_data) < 20:
            return {"stride_length": 0.0, "step_length": 0.0}
        
        # Get foot positions
        left_foot = self.get_landmark_positions(pose_data, MediaPipeLandmarks.LEFT_ANKLE.value)
        right_foot = self.get_landmark_positions(pose_data, MediaPipeLandmarks.RIGHT_ANKLE.value)
        
        # Smooth positions
        left_foot_smooth = np.array([
            self.smooth_signal(left_foot[:, 0]),
            self.smooth_signal(left_foot[:, 1]),
            self.smooth_signal(left_foot[:, 2])
        ]).T
        
        right_foot_smooth = np.array([
            self.smooth_signal(right_foot[:, 0]),
            self.smooth_signal(right_foot[:, 1]),
            self.smooth_signal(right_foot[:, 2])
        ]).T
        
        # Find foot contacts (peaks in negative y direction)
        left_contacts, _ = find_peaks(-left_foot_smooth[:, 1], height=0.01, distance=5)
        right_contacts, _ = find_peaks(-right_foot_smooth[:, 1], height=0.01, distance=5)
        
        if len(left_contacts) < 2 or len(right_contacts) < 2:
            # Fallback to anatomical estimates
            stride_length = self.height_m * RunningConstants.AVERAGE_STRIDE_HEIGHT_RATIO
            step_length = self.height_m * RunningConstants.AVERAGE_STEP_HEIGHT_RATIO
            
            return {
                "stride_length": stride_length,
                "step_length": step_length,
                "measurement_method": "anatomical_estimate"
            }
        
        # Calculate stride lengths (same foot consecutive contacts)
        left_strides = []
        for i in range(len(left_contacts) - 1):
            pos1 = left_foot_smooth[left_contacts[i]]
            pos2 = left_foot_smooth[left_contacts[i + 1]]
            stride_dist = self.calculate_distance(pos1, pos2)
            left_strides.append(stride_dist)
        
        right_strides = []
        for i in range(len(right_contacts) - 1):
            pos1 = right_foot_smooth[right_contacts[i]]
            pos2 = right_foot_smooth[right_contacts[i + 1]]
            stride_dist = self.calculate_distance(pos1, pos2)
            right_strides.append(stride_dist)
        
        # Calculate step lengths (alternating feet)
        all_contacts = sorted(
            [(frame, 'left') for frame in left_contacts] + 
            [(frame, 'right') for frame in right_contacts]
        )
        
        steps = []
        for i in range(len(all_contacts) - 1):
            frame1, foot1 = all_contacts[i]
            frame2, foot2 = all_contacts[i + 1]
            
            if foot1 != foot2:  # Alternating feet
                pos1 = left_foot_smooth[frame1] if foot1 == 'left' else right_foot_smooth[frame1]
                pos2 = left_foot_smooth[frame2] if foot2 == 'left' else right_foot_smooth[frame2]
                step_dist = self.calculate_distance(pos1, pos2)
                steps.append(step_dist)
        
        # Convert to real-world units
        pixel_to_meter_ratio = self.height_m / np.mean([
            np.abs(left_foot[:, 1].max() - left_foot[:, 1].min()),
            np.abs(right_foot[:, 1].max() - right_foot[:, 1].min())
        ])
        
        # Calculate averages
        all_strides = left_strides + right_strides
        avg_stride_length = np.mean(all_strides) * pixel_to_meter_ratio if all_strides else 0.0
        avg_step_length = np.mean(steps) * pixel_to_meter_ratio if steps else 0.0
        
        return {
            "stride_length": avg_stride_length,
            "step_length": avg_step_length,
            "stride_count": len(all_strides),
            "step_count": len(steps),
            "measurement_method": "pose_analysis"
        }
