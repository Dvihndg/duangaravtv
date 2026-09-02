from datetime import datetime, timedelta

def test_create_and_list_appointment(client, auth_headers):
    # 1. Create appointment
    response = client.post(
        "/api/v1/appointments",
        json={
            "vehicle_id": 1,
            "appointment_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "notes": "Kiểm tra hệ thống phanh"
        },
        headers=auth_headers
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["vehicle_id"] == 1
    assert data["status"] == "pending"

    # 2. List appointments
    response = client.get("/api/v1/appointments", headers=auth_headers)
    assert response.status_code == 200
    apts = response.json()
    assert len(apts) >= 1

def test_update_appointment_status(client, auth_headers):
    # Create apt
    response = client.post(
        "/api/v1/appointments",
        json={
            "vehicle_id": 1,
            "appointment_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "notes": "Bảo dưỡng 10k km"
        },
        headers=auth_headers
    )
    apt_id = response.json()["id"]

    # Update status to confirmed
    update_res = client.put(
        f"/api/v1/appointments/{apt_id}",
        json={"status": "confirmed"},
        headers=auth_headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "confirmed"
