import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.report import Report
from app.models.recipient import Recipient
from app.models.delivery_log import DeliveryLog
from app.services.pdf_generator import pdf_generator
from app.services.whatsapp_client import (
    whatsapp_client,
    WhatsAppConfigurationError,
    WhatsAppAPIError
)

logger = logging.getLogger(__name__)


class ReportService:
    """Orchestration service for report generation, storage, and WhatsApp Cloud API distribution."""

    def generate_and_distribute_report(
        self,
        db: Session,
        title: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        distribute: bool = True,
        custom_metrics: Optional[Dict[str, Any]] = None
    ) -> Report:
        """
        Executes end-to-end report generation:
        1. Generates professional PDF report via ReportLab.
        2. Persists report metadata to database.
        3. Uploads media to Meta Cloud API.
        4. Dispatches document to all opted-in recipients.
        5. Logs individual delivery states.
        """
        logger.info("Initiating weekly report generation cycle...")

        # 1. Generate PDF
        file_path, file_name, file_size, start_time, end_time, metrics = pdf_generator.generate_weekly_report(
            title=title,
            period_start=period_start,
            period_end=period_end,
            custom_metrics=custom_metrics
        )

        # 2. Persist Report record
        report = Report(
            title=title or "Weekly Performance & Operations Report",
            reporting_period_start=start_time,
            reporting_period_end=end_time,
            file_path=file_path,
            file_name=file_name,
            file_size_bytes=file_size,
            metrics_data=json.dumps(metrics),
            status="generated",
            generated_at=datetime.utcnow()
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        logger.info(f"Persisted Report #{report.id} to database. File: {file_name}")

        if not distribute:
            logger.info("Report distribution was skipped by request parameter.")
            return report

        # 3. Fetch active opted-in recipients
        recipients = db.query(Recipient).filter(
            Recipient.is_active.is_(True),
            Recipient.opted_in.is_(True)
        ).all()

        if not recipients:
            logger.info("No active opted-in recipients found for distribution.")
            return report

        # 4. WhatsApp Cloud API Upload & Delivery
        if not settings.is_whatsapp_configured:
            msg = (
                "WhatsApp Cloud API credentials not configured in environment. "
                "Report PDF generated and saved locally, but not dispatched to WhatsApp."
            )
            logger.warning(msg)
            report.status = "generated"
            report.error_message = msg

            # Record pending delivery logs
            for recipient in recipients:
                log = DeliveryLog(
                    report_id=report.id,
                    recipient_id=recipient.id,
                    phone_number=recipient.phone_number,
                    delivery_channel="whatsapp_cloud_api",
                    status="pending_credentials",
                    error_message="Meta credentials not configured; PDF available for local download.",
                    sent_at=None
                )
                db.add(log)
            db.commit()
            return report

        try:
            # Upload media to Meta Cloud API
            media_id = whatsapp_client.upload_media(file_path, mime_type="application/pdf")
            report.media_id = media_id
            report.status = "uploaded"
            db.commit()

            # Disseminate to recipients
            period_label = f"{start_time.strftime('%b %d')} - {end_time.strftime('%b %d, %Y')}"
            caption = f"📊 *Weekly Operations & Performance Digest*\nPeriod: {period_label}\nAttached is your official executive summary."

            delivered_count = 0
            failed_count = 0

            for recipient in recipients:
                try:
                    res = whatsapp_client.send_document_message(
                        recipient_phone=recipient.phone_number,
                        media_id=media_id,
                        filename=file_name,
                        caption=caption
                    )
                    wamid = res.get("messages", [{}])[0].get("id")

                    log = DeliveryLog(
                        report_id=report.id,
                        recipient_id=recipient.id,
                        phone_number=recipient.phone_number,
                        message_id=wamid,
                        delivery_channel="whatsapp_cloud_api",
                        status="sent",
                        sent_at=datetime.utcnow(),
                        meta_response=json.dumps(res)
                    )
                    db.add(log)
                    delivered_count += 1
                except Exception as send_err:
                    logger.error(f"Failed to deliver report to {recipient.phone_number}: {send_err}")
                    log = DeliveryLog(
                        report_id=report.id,
                        recipient_id=recipient.id,
                        phone_number=recipient.phone_number,
                        delivery_channel="whatsapp_cloud_api",
                        status="failed",
                        error_message=str(send_err),
                        sent_at=datetime.utcnow()
                    )
                    db.add(log)
                    failed_count += 1

            report.status = "sent" if delivered_count > 0 else "failed"
            db.commit()
            logger.info(f"Report #{report.id} distribution complete. Sent: {delivered_count}, Failed: {failed_count}")

        except Exception as upload_err:
            logger.error(f"Error during Meta media upload: {upload_err}")
            report.status = "failed"
            report.error_message = str(upload_err)
            db.commit()

        return report


report_service = ReportService()
