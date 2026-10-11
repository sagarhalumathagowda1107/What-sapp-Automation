from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.schedule import Schedule
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleListResponse
)
from app.services.scheduler_service import scheduler_service

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.post(
    "",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Automated Report Schedule"
)
def create_schedule(payload: ScheduleCreate, db: Session = Depends(get_db)):
    """Creates a new automated weekly reporting schedule."""
    schedule = Schedule(**payload.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    # Sync APScheduler
    scheduler_service.sync_jobs()
    return schedule


@router.get(
    "",
    response_model=ScheduleListResponse,
    summary="List Reporting Schedules"
)
def list_schedules(db: Session = Depends(get_db)):
    """Retrieves all reporting schedule configurations."""
    items = db.query(Schedule).order_by(Schedule.id.asc()).all()
    return ScheduleListResponse(total=len(items), items=items)


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Get Schedule by ID"
)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Retrieves single schedule by ID."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail=f"Schedule with ID {schedule_id} not found.")
    return schedule


@router.put(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Update Schedule"
)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdate,
    db: Session = Depends(get_db)
):
    """Updates schedule parameters and re-synchronizes the APScheduler trigger."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail=f"Schedule with ID {schedule_id} not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)

    db.commit()
    db.refresh(schedule)

    scheduler_service.sync_jobs()
    return schedule


@router.post(
    "/{schedule_id}/run",
    summary="Manually Trigger Immediate Schedule Run"
)
def run_schedule_now(schedule_id: int, db: Session = Depends(get_db)):
    """
    Forces immediate execution of the specified schedule.
    Bypasses duplicate window check.
    """
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail=f"Schedule with ID {schedule_id} not found.")

    result = scheduler_service.trigger_now(schedule_id=schedule_id)
    return {
        "message": f"Manual trigger executed for schedule '{schedule.name}'.",
        "result": result
    }
