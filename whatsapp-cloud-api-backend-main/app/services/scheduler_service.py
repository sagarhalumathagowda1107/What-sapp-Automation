import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    def ZoneInfo(tz_name):
        return pytz.timezone(tz_name)

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.schedule import Schedule
from app.models.report import Report
from app.services.report_service import report_service

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    APScheduler Management Service configured for Asia/Kolkata timezone.
    Enforces concurrency locking, duplicate suppression, and resilient execution.
    """

    def __init__(self):
        self.timezone_name = settings.TIMEZONE
        try:
            self.tz = ZoneInfo(self.timezone_name)
        except Exception:
            self.tz = ZoneInfo("Asia/Kolkata")

        self.scheduler = BackgroundScheduler(timezone=self.tz)
        self._lock = threading.Lock()
        self.job_id = "weekly_report_job"

    def start(self):
        """Initializes and starts the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("APScheduler background scheduler started.")
            self.sync_jobs()

    def shutdown(self):
        """Gracefully terminates the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("APScheduler background scheduler shut down.")

    def sync_jobs(self):
        """
        Synchronizes scheduled jobs from database or default settings.
        Prevents duplicate jobs by using replace_existing=True.
        """
        db = SessionLocal()
        try:
            active_schedule = db.query(Schedule).filter(Schedule.is_active.is_(True)).first()

            if active_schedule:
                day_of_week = active_schedule.day_of_week
                hour = active_schedule.hour
                minute = active_schedule.minute
                schedule_id = active_schedule.id
                name = active_schedule.name
            else:
                day_of_week = settings.SCHEDULE_DAY_OF_WEEK
                hour = settings.SCHEDULE_HOUR
                minute = settings.SCHEDULE_MINUTE
                schedule_id = None
                name = "Default Weekly Schedule"

            trigger = CronTrigger(
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
                timezone=self.tz
            )

            self.scheduler.add_job(
                func=self.execute_scheduled_report,
                trigger=trigger,
                id=self.job_id,
                name=f"Weekly PDF Report Job ({name})",
                replace_existing=True,
                max_instances=1,
                kwargs={"schedule_id": schedule_id}
            )

            job = self.scheduler.get_job(self.job_id)
            next_run = job.next_run_time if job else None
            logger.info(
                f"Configured scheduler job: day={day_of_week}, time={hour:02d}:{minute:02d} "
                f"{self.timezone_name}. Next run at: {next_run}"
            )

            # Update next_run_at in database if schedule entity exists
            if active_schedule and next_run:
                active_schedule.next_run_at = next_run
                db.commit()

        except Exception as e:
            logger.error(f"Error synchronizing scheduler jobs: {e}")
        finally:
            db.close()

    def execute_scheduled_report(self, schedule_id: Optional[int] = None, force: bool = False) -> Dict[str, Any]:
        """
        Executes report generation job.
        Uses in-memory mutex to prevent concurrent runs, and checks recent runs to prevent duplicate reports.
        """
        if not self._lock.acquire(blocking=False):
            logger.warning("Scheduled report execution skipped: Another job instance is actively executing.")
            return {"status": "skipped", "reason": "Job currently in progress"}

        db = SessionLocal()
        try:
            now = datetime.now(self.tz)
            logger.info(f"Executing scheduled report run at {now.isoformat()} ({self.timezone_name})")

            # Duplicate prevention: Check if report was already generated within the last 18 hours
            if not force:
                cutoff = datetime.utcnow() - timedelta(hours=18)
                recent_report = db.query(Report).filter(
                    Report.generated_at >= cutoff,
                    Report.status.in_(["generated", "uploaded", "sent"])
                ).first()

                if recent_report:
                    logger.info(
                        f"Skipping duplicate run. Report #{recent_report.id} was already generated recently "
                        f"at {recent_report.generated_at} UTC."
                    )
                    return {"status": "skipped", "reason": "Report already generated for this cycle", "report_id": recent_report.id}

            # Generate and disseminate
            report = report_service.generate_and_distribute_report(
                db=db,
                title=f"Weekly Executive Digest ({now.strftime('%b %d, %Y')})",
                distribute=True
            )

            # Update schedule tracking
            if schedule_id:
                sch = db.query(Schedule).filter(Schedule.id == schedule_id).first()
                if sch:
                    sch.last_run_at = datetime.utcnow()
                    job = self.scheduler.get_job(self.job_id)
                    if job and job.next_run_time:
                        sch.next_run_at = job.next_run_time
                    db.commit()

            return {
                "status": "success",
                "report_id": report.id,
                "file_name": report.file_name,
                "report_status": report.status
            }

        except Exception as e:
            logger.error(f"Error during scheduled report execution: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}
        finally:
            self._lock.release()
            db.close()

    def trigger_now(self, schedule_id: Optional[int] = None) -> Dict[str, Any]:
        """Manually trigger immediate execution."""
        return self.execute_scheduled_report(schedule_id=schedule_id, force=True)

    def get_status(self) -> Dict[str, Any]:
        """Retrieve scheduler operational state."""
        job = self.scheduler.get_job(self.job_id) if self.scheduler.running else None
        return {
            "running": self.scheduler.running,
            "timezone": str(self.timezone_name),
            "job_id": self.job_id,
            "next_run_time": job.next_run_time.isoformat() if job and job.next_run_time else None,
            "is_locked": self._lock.locked()
        }


scheduler_service = SchedulerService()
