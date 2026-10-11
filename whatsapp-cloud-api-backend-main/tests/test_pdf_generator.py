import os
from datetime import datetime, timedelta
from app.services.pdf_generator import pdf_generator


def test_generate_weekly_pdf_creates_valid_file():
    """Verify that ReportLab builds a valid PDF with metadata and non-zero byte size."""
    now = datetime.utcnow()
    start = now - timedelta(days=7)
    custom_metrics = {
        "total_revenue": 195000.50,
        "active_subscribers": 1500,
        "growth_rate": 18.2
    }

    file_path, file_name, file_size, s_time, e_time, metrics = pdf_generator.generate_weekly_report(
        title="Test Corporate Weekly Report",
        period_start=start,
        period_end=now,
        custom_metrics=custom_metrics
    )

    assert os.path.exists(file_path), "Generated PDF file must exist on disk"
    assert file_size > 0, "PDF file size must be greater than 0"
    assert file_name.endswith(".pdf")
    assert metrics["total_revenue"] == 195000.50
    assert metrics["growth_rate"] == 18.2

    # Clean up test artifact
    if os.path.exists(file_path):
        os.remove(file_path)
