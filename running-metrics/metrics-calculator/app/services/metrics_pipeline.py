from typing import List, Dict, Any

from shared.models.domain import (
    RunnerProfile,
    FramePose,
    RunningMetrics,
)

from ..calculators.cadence_calculator import CadenceCalculator
from ..calculators.speed_calculator import SpeedCalculator
from ..calculators.stride_calculator import StrideCalculator
from ..calculators.timing_calculator import TimingCalculator
from ..calculators.vertical_oscillation_calculator import VerticalOscillationCalculator
from ..calculators.lean_angle_calculator import LeanAngleCalculator
from ..calculators.symmetry_calculator import SymmetryCalculator
from ..calculators.center_of_gravity_calculator import CenterOfGravityCalculator
from ..calculators.joint_angle_calculator import JointAngleCalculator


class MetricsPipeline:
    """Runs a set of metrics calculators and merges their outputs into RunningMetrics."""

    def __init__(self, runner_profile: RunnerProfile):
        self.calculators = [
            CadenceCalculator(runner_profile),
            SpeedCalculator(runner_profile),
            StrideCalculator(runner_profile),
            TimingCalculator(runner_profile),
            VerticalOscillationCalculator(runner_profile),
            LeanAngleCalculator(runner_profile),
            SymmetryCalculator(runner_profile),
            CenterOfGravityCalculator(runner_profile),
            JointAngleCalculator(runner_profile),
        ]

    def run(self, pose_data: List[FramePose]) -> RunningMetrics:
        """Execute all calculators and combine their results."""
        merged: Dict[str, Any] = {}
        for calc in self.calculators:
            try:
                calc_result = calc.calculate(pose_data)
                merged.update(calc_result)
            except Exception:
                # Keep pipeline robust – ignore individual calc failures
                continue

        # Provide defaults for any missing fields required by RunningMetrics
        defaults = {
            "cadence": 0.0,
            "speed": 0.0,
            "step_length": 0.0,
            "stride_length": 0.0,
            "ground_contact_time": 0.0,
            "flight_time": 0.0,
            "vertical_oscillation": 0.0,
            "forward_lean": 0.0,
            "left_right_symmetry": 0.0,
            "center_of_gravity": {"x": 0.0, "y": 0.0, "z": 0.0},
            "joint_angles": {},
        }

        for k, v in defaults.items():
            merged.setdefault(k, v)

        # RunningMetrics model validates types/constraints
        metrics = RunningMetrics(**merged)
        return metrics 