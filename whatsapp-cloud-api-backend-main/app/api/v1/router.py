from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.reports import router as reports_router
from app.api.v1.schedules import router as schedules_router
from app.api.v1.recipients import router as recipients_router
from app.api.v1.delivery_logs import router as delivery_logs_router
from app.api.v1.webhook import router as webhook_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(schedules_router)
api_v1_router.include_router(recipients_router)
api_v1_router.include_router(delivery_logs_router)
api_v1_router.include_router(webhook_router)
