from enum import Enum


class GaitEvent(Enum):
    FOOT_STRIKE = "foot_strike"
    TOE_OFF = "toe_off"
    METRICS_CALCULATED = "metrics_calculated"
    ANALYSIS_COMPLETE = "analysis_complete"
