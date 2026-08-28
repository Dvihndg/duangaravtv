def test_ai_history_summary(client, auth_headers):
    # Test valid vehicle
    res = client.post(
        "/api/v1/ai/summarize-history",
        json={"vehicle_id": 1},
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["output"]) > 0

def test_ai_service_explainer(client, auth_headers):
    # Create RO
    ro_res = client.post(
        "/api/v1/repair-orders",
        json={"vehicle_id": 1, "initial_symptoms": "Xe giật khi tăng tốc"},
        headers=auth_headers
    )
    ro_id = ro_res.json()["id"]

    # Call AI service explainer
    res = client.post(
        "/api/v1/ai/explain-services",
        json={"repair_order_id": ro_id},
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["output"]) > 0

def test_ai_draft_quotation(client, auth_headers):
    # Create RO & add items
    ro_res = client.post(
        "/api/v1/repair-orders",
        json={"vehicle_id": 1, "initial_symptoms": "Bảo dưỡng 40k km"},
        headers=auth_headers
    )
    ro_id = ro_res.json()["id"]

    client.post(
        f"/api/v1/repair-orders/{ro_id}/items",
        json={
            "item_type": "service",
            "name": "Thay dầu máy",
            "quantity": 1,
            "unit_price": 0,
            "labor_cost": 150000.0
        },
        headers=auth_headers
    )

    # Call AI Draft Quotation
    res = client.post(
        "/api/v1/ai/draft-quotation",
        json={"repair_order_id": ro_id},
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["output"]) > 0


def test_ai_assistant(client, auth_headers):
    # Test free-form question without RO
    res = client.post(
        "/api/v1/ai/assistant",
        json={"question": "Thay phanh trước xe Camry hết bao nhiêu tiền?"},
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["output"]) > 0

    # Test free-form question with RO context
    ro_res = client.post(
        "/api/v1/repair-orders",
        json={"vehicle_id": 1, "initial_symptoms": "Kêu gầm xe"},
        headers=auth_headers
    )
    ro_id = ro_res.json()["id"]

    res_ro = client.post(
        "/api/v1/ai/assistant",
        json={
            "question": "Hãy giải thích và lập báo giá nháp dịch vụ cho phiếu này",
            "repair_order_id": ro_id
        },
        headers=auth_headers
    )
    assert res_ro.status_code == 200
    data_ro = res_ro.json()
    assert data_ro["success"] is True
    assert len(data_ro["output"]) > 0


def test_ai_edge_cases(client, auth_headers):
    # 1. Non-existent vehicle_id
    res_veh = client.post(
        "/api/v1/ai/summarize-history",
        json={"vehicle_id": 99999},
        headers=auth_headers
    )
    assert res_veh.status_code == 400
    assert "Không tìm thấy" in res_veh.json()["detail"]

    # 2. Non-existent repair_order_id for service explainer
    res_ro = client.post(
        "/api/v1/ai/explain-services",
        json={"repair_order_id": 99999},
        headers=auth_headers
    )
    assert res_ro.status_code == 400
    assert "Không tìm thấy" in res_ro.json()["detail"]

    # 3. Non-existent repair_order_id for draft quotation
    res_quo = client.post(
        "/api/v1/ai/draft-quotation",
        json={"repair_order_id": 99999},
        headers=auth_headers
    )
    assert res_quo.status_code == 400
    assert "Không tìm thấy" in res_quo.json()["detail"]

