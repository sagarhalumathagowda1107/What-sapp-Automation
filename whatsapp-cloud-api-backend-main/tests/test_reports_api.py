import os
from unittest.mock import patch


def test_generate_and_download_report_api(client):
    """Test generating a report through API and downloading the resulting PDF."""
    generate_payload = {
        "title": "API Test Weekly Executive Report",
        "distribute_to_recipients": False,
        "custom_metrics": {
            "total_revenue": 125000.0,
            "active_subscribers": 890
        }
    }

    # 1. Generate Report
    gen_res = client.post("/reports/generate", json=generate_payload)
    assert gen_res.status_code == 201
    data = gen_res.json()
    assert data["id"] is not None
    assert data["file_name"].endswith(".pdf")
    assert data["status"] == "generated"
    report_id = data["id"]
    file_path = data["file_path"]

    # 2. Get Report by ID
    get_res = client.get(f"/reports/{report_id}")
    assert get_res.status_code == 200
    report_detail = get_res.json()
    assert report_detail["title"] == "API Test Weekly Executive Report"

    # 3. List Reports
    list_res = client.get("/reports")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 4. Download Report
    down_res = client.get(f"/reports/{report_id}/download")
    assert down_res.status_code == 200
    assert down_res.headers["content-type"] == "application/pdf"
    assert len(down_res.content) > 0

    # Cleanup generated file
    if os.path.exists(file_path):
        os.remove(file_path)
