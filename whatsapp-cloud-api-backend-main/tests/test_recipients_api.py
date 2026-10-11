def test_create_and_list_recipients(client):
    """Test registering a recipient and fetching from recipient list."""
    payload = {
        "name": "Jane Doe",
        "phone_number": "+91 98765 43210",
        "email": "jane@example.com",
        "department": "Finance",
        "is_active": True,
        "opted_in": True,
        "timezone": "Asia/Kolkata"
    }

    # 1. Create recipient
    create_res = client.post("/recipients", json=payload)
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["name"] == "Jane Doe"
    assert data["phone_number"] == "919876543210"  # Normalized E.164 without plus
    assert data["opted_in"] is True
    recipient_id = data["id"]

    # 2. Prevent duplicate phone registration
    dup_res = client.post("/recipients", json=payload)
    assert dup_res.status_code == 400

    # 3. Retrieve single recipient
    get_res = client.get(f"/recipients/{recipient_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Jane Doe"

    # 4. List recipients
    list_res = client.get("/recipients")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1


def test_invalid_phone_number_rejected(client):
    """Verify phone numbers with fewer than 10 digits are rejected."""
    bad_payload = {
        "name": "Invalid User",
        "phone_number": "123",
        "is_active": True,
        "opted_in": True
    }
    res = client.post("/recipients", json=bad_payload)
    assert res.status_code == 422
