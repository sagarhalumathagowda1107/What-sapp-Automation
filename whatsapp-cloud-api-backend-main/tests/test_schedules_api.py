from unittest.mock import patch


def test_create_and_run_schedule(client):
    """Test creating a schedule and triggering it manually."""
    schedule_payload = {
        "name": "Weekly Monday Performance Run",
        "description": "Executive PDF summary every Monday at 9:00 AM IST",
        "day_of_week": "mon",
        "hour": 9,
        "minute": 0,
        "timezone": "Asia/Kolkata",
        "is_active": True
    }

    # 1. Create schedule
    create_res = client.post("/schedules", json=schedule_payload)
    assert create_res.status_code == 201
    schedule_id = create_res.json()["id"]

    # 2. List schedules
    list_res = client.get("/schedules")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 3. Trigger run with mocked report service
    with patch("app.services.scheduler_service.scheduler_service.trigger_now") as mock_trigger:
        mock_trigger.return_value = {"status": "success", "report_id": 1}
        run_res = client.post(f"/schedules/{schedule_id}/run")
        assert run_res.status_code == 200
        assert "Manual trigger executed" in run_res.json()["message"]
