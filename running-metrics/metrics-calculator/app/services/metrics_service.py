import logging
from typing import Callable, List
from uuid import UUID

from shared.database.repository import (
    RunningSessionRepository,
    PoseDataRepository,
    RunningMetricsRepository,
)
from shared.models.domain import (
    RunnerProfile,
    FramePose,
    PoseLandmark,
    ProcessingStatus,
)
from .metrics_pipeline import MetricsPipeline

# Lazy import to avoid heavy dependency in scope
from shared.events.event_bus import EventBus

logger = logging.getLogger(__name__)


class MetricsService:
    """Coordinates metrics calculation using MetricsPipeline and DB repositories."""

    def __init__(
        self,
        session_repository: RunningSessionRepository,
        pose_repository: PoseDataRepository,
        metrics_repository: RunningMetricsRepository,
        event_bus: "EventBus | None" = None,
    ):
        self.session_repository = session_repository
        self.pose_repository = pose_repository
        self.metrics_repository = metrics_repository
        self.event_bus = event_bus

    async def compute_metrics_for_session(self, session_id: UUID):
        """Fetch pose data for a session, run pipeline, store metrics, and update session."""
        session_db = await self.session_repository.get_by_id(session_id)
        if not session_db:
            raise ValueError(f"Session not found: {session_id}")

        # Build RunnerProfile
        runner_profile = RunnerProfile(
            gender=session_db.runner_gender,
            height_cm=session_db.runner_height_cm,
            age=session_db.runner_age,
            email=session_db.runner_email,
        )

        # Fetch pose data
        pose_db_list = await self.pose_repository.get_by_session_id(session_id)
        pose_data: List[FramePose] = []
        for pose_db in pose_db_list:
            landmarks = [
                PoseLandmark(
                    x=lm["x"],
                    y=lm["y"],
                    z=lm["z"],
                    visibility=lm["visibility"],
                )
                for lm in pose_db.landmarks
            ]
            pose_data.append(
                FramePose(
                    frame_number=pose_db.frame_number,
                    timestamp=pose_db.timestamp,
                    landmarks=landmarks,
                    confidence=pose_db.confidence,
                )
            )

        # Run pipeline
        pipeline = MetricsPipeline(runner_profile)
        metrics = pipeline.run(pose_data)

        # Persist metrics
        metrics_db = self._to_db_model(metrics, session_id)
        await self.metrics_repository.create(metrics_db)

        # Update session status
        session_db.status = ProcessingStatus.COMPLETED
        await self.session_repository.update(session_db)

        # Publish event
        if self.event_bus:
            from shared.models.events import MetricsCalculatedEvent
            from datetime import datetime
            from uuid import uuid4

            event = MetricsCalculatedEvent(
                event_id=uuid4(),
                timestamp=datetime.utcnow(),
                session_id=session_id,
                data={"metrics_keys": list(metrics.dict().keys())},
            )
            try:
                await self.event_bus.publish(event)  # type: ignore[attr-defined]
            except Exception as pub_err:
                logger.warning(f"Failed to publish MetricsCalculatedEvent: {pub_err}")

        logger.info(f"Metrics calculated and stored for session {session_id}")
        return metrics

    def _to_db_model(self, metrics, session_id: UUID):
        """Convert RunningMetrics pydantic model to DB model instance."""
        from shared.database.models import RunningMetricsDB  # local import to avoid circular

        return RunningMetricsDB(
            session_id=session_id,
            cadence=metrics.cadence,
            speed=metrics.speed,
            step_length=metrics.step_length,
            stride_length=metrics.stride_length,
            ground_contact_time=metrics.ground_contact_time,
            flight_time=metrics.flight_time,
            vertical_oscillation=metrics.vertical_oscillation,
            forward_lean=metrics.forward_lean,
            left_right_symmetry=metrics.left_right_symmetry,
            center_of_gravity=metrics.center_of_gravity,
            joint_angles=metrics.joint_angles,
        ) 