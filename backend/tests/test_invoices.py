def test_invoice_and_payment(client, auth_headers):
    # Create RO
    ro_res = client.post(
        "/api/v1/repair-orders",
        json={"vehicle_id": 1, "mileage_at_reception": 25000},
        headers=auth_headers
    )
    ro_id = ro_res.json()["id"]

    # Add item
    client.post(
        f"/api/v1/repair-orders/{ro_id}/items",
        json={
            "item_type": "service",
            "name": "Bảo dưỡng tổng thể",
            "quantity": 1,
            "unit_price": 500000.0,
            "labor_cost": 200000.0
        },
        headers=auth_headers
    )

    # 1. Create Invoice
    inv_res = client.post(
        f"/api/v1/repair-orders/{ro_id}/invoice?discount_amount=50000",
        headers=auth_headers
    )
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert inv_data["subtotal"] == 700000.0
    assert inv_data["discount_amount"] == 50000.0
    # taxable = 650,000, tax 8% = 52,000, total = 702,000
    assert inv_data["total_amount"] == 702000.0
    assert inv_data["status"] == "unpaid"
    inv_id = inv_data["id"]

    # 2. Record Payment
    pay_res = client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "payment_method": "cash",
            "amount": 702000.0,
            "transaction_reference": "CASH-001"
        },
        headers=auth_headers
    )
    assert pay_res.status_code == 200

    # 3. Verify Invoice status is now PAID
    inv_check = client.get(f"/api/v1/invoices/{inv_id}", headers=auth_headers)
    assert inv_check.json()["status"] == "paid"
    assert inv_check.json()["balance_due"] == 0.0
