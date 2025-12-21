from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any


logger = logging.getLogger(__name__)


class ScheduledAction:
    def __init__(self, action_name, user_id, frequency):
        self.action_name = action_name
        self.user_id = user_id
        self.frequency = frequency  # "daily" or "weekly"
        self.last_run = None

    def due(self):
        if not self.last_run:
            return True
        delta = timedelta(days=1 if self.frequency == "daily" else 7)
        return datetime.utcnow() - self.last_run >= delta


class AIScheduler:
    """
    Phase 1 scheduler: in-memory, safe, no persistence.
    """

    def __init__(self):
        self.jobs: List[ScheduledAction] = []

    def add_job(self, job: ScheduledAction):
        self.jobs.append(job)

    def run_due(self, engine, actions: Dict[str, Dict[str, Any]]):
        """
        Execute all due jobs using existing action handlers.

        Phase 1 behavior:
        - READ-ONLY execution of existing actions
        - Log results only (no notifications)
        - Never raises to callers
        """
        for job in list(self.jobs):
            try:
                if not job.due():
                    continue

                action_def = actions.get(job.action_name)
                if not action_def:
                    logger.warning(
                        "AIScheduler: unknown action '%s' for user_id=%s",
                        job.action_name,
                        job.user_id,
                    )
                    continue

                handler = action_def.get("handler")
                if not callable(handler):
                    logger.warning(
                        "AIScheduler: non-callable handler for action '%s'", job.action_name
                    )
                    continue

                logger.info(
                    "AIScheduler: running scheduled action '%s' for user_id=%s",
                    job.action_name,
                    job.user_id,
                )
                # Phase 1: pass user=None; handlers are read-only and RBAC is enforced
                # at scheduling time, not execution time.
                result = handler(user=None)
                job.last_run = datetime.utcnow()
                logger.info(
                    "AIScheduler: action '%s' for user_id=%s completed (success=%s)",
                    job.action_name,
                    job.user_id,
                    bool(result),
                )
            except Exception as e:  # pragma: no cover - defensive
                logger.warning(
                    "AIScheduler: error running scheduled action '%s' for user_id=%s: %s",
                    job.action_name,
                    job.user_id,
                    e,
                )


# Single global in-memory scheduler instance
ai_scheduler = AIScheduler()


