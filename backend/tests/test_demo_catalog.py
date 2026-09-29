from backend.app.demo_catalog import DEMO_PARTS, DEMO_SERVICES


def test_demo_service_combos_have_prices_and_duration():
    combos = [row for row in DEMO_SERVICES if row[0].startswith("CB-DV-")]
    assert len(combos) == 6
    assert {row[0] for row in combos} == {f"CB-DV-{i:03d}" for i in range(1, 7)}
    assert all(row[3] > 0 and row[4] > 0 for row in combos)


def test_demo_warehouse_combos_have_sell_cost_stock_and_minimum():
    combos = [row for row in DEMO_PARTS if row[0].startswith("CB-KHO-")]
    assert len(combos) == 6
    assert all(row[5] > row[6] > 0 for row in combos)
    assert all(row[7] >= row[8] > 0 for row in combos)


def test_demo_loose_parts_cover_multiple_categories_with_prices():
    parts = [row for row in DEMO_PARTS if row[0].startswith("PT-") and int(row[0].split("-")[1]) >= 21]
    assert len(parts) == 20
    categories = {row[3] for row in parts}
    assert {"Lọc", "Phanh", "Gầm", "Động cơ", "Điện ô tô", "Điều hòa"}.issubset(categories)
    assert all(row[5] > row[6] > 0 for row in parts)
    assert all(row[7] >= 0 and row[8] > 0 for row in parts)
