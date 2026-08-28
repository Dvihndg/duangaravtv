def test_repair_order_lifecycle(client, auth_headers):
    # 1. Create Repair Order
    ro_res = client.post(
        "/api/v1/repair-orders",
        json={
            "vehicle_id": 1,
            "mileage_at_reception": 50000,
            "initial_symptoms": "Động cơ kêu to khi rồ ga"
        },
        headers=auth_headers
    )
    assert ro_res.status_code == 200
    ro_data = ro_res.json()
    ro_id = ro_data["id"]
    assert ro_data["status"] == "received"

    # 2. Add service item
    item_res = client.post(
        f"/api/v1/repair-orders/{ro_id}/items",
        json={
            "item_type": "service",
            "service_id": 1,
            "name": "Test Service",
            "quantity": 1,
            "unit_price": 0,
            "labor_cost": 100000.0
        },
        headers=auth_headers
    )
    assert item_res.status_code == 200
    assert item_res.json()["total_price"] == 100000.0

    # 3. Add part item
    part_item_res = client.post(
        f"/api/v1/repair-orders/{ro_id}/items",
        json={
            "item_type": "part",
            "part_id": 1,
            "name": "Test Part",
            "quantity": 2,
            "unit_price": 500000.0,
            "labor_cost": 0
        },
        headers=auth_headers
    )
    assert part_item_res.status_code == 200
    assert part_item_res.json()["total_price"] == 1000000.0

    # 4. Check updated total
    get_ro = client.get(f"/api/v1/repair-orders/{ro_id}", headers=auth_headers)
    assert get_ro.status_code == 200
    assert get_ro.json()["final_cost"] == 1100000.0

    # 5. Update status to IN_PROGRESS
    status_res = client.put(
        f"/api/v1/repair-orders/{ro_id}",
        json={"status": "in_progress", "technical_diagnosis": "Cần thay lọc gió và vệ sinh cổ hút"},
        headers=auth_headers
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "in_progress"
