import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.database import Base, engine, get_db
from backend.app.models import User, UserRole, Part, Service
from backend.app.auth import get_password_hash, create_access_token

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db_session = Session(bind=engine)
    
    # Ensure test user
    user = db_session.query(User).filter(User.username == "test_scenarios_admin").first()
    if not user:
        user = User(
            username="test_scenarios_admin",
            email="scenarios_admin@garage.vtv",
            hashed_password=get_password_hash("admin123"),
            full_name="Scenarios Admin",
            role=UserRole.MANAGER
        )
        db_session.add(user)
        
    # Ensure test parts
    oil = db_session.query(Part).filter(Part.code == "PAR-OIL-001").first()
    if not oil:
        oil = Part(code="PAR-OIL-001", name="Dầu nhớt động cơ Synthetic 4L", unit_price=250000, stock_quantity=25)
        db_session.add(oil)

    fil = db_session.query(Part).filter(Part.code == "PAR-FIL-001").first()
    if not fil:
        fil = Part(code="PAR-FIL-001", name="Lọc nhớt động cơ chính hãng", unit_price=150000, stock_quantity=18)
        db_session.add(fil)

    # Ensure test services
    brake_srv = db_session.query(Service).filter(Service.code == "SER-002").first()
    if not brake_srv:
        brake_srv = Service(code="SER-002", name="Láng đĩa phanh ô tô", labor_cost=400000)
        db_session.add(brake_srv)

    db_session.commit()
    yield db_session
    db_session.close()

@pytest.fixture
def auth_headers(db):
    user = db.query(User).filter(User.username == "test_scenarios_admin").first()
    token = create_access_token({"sub": user.username, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}

def test_demo_scenarios_all_5(auth_headers):
    client = TestClient(app)
    
    for s_id in range(1, 6):
        res = client.post(f"/api/v1/ai/demo-scenarios/{s_id}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["scenario_id"] == s_id
        assert "status" in data
        assert "estimated_total" in data
        assert data["estimated_total"] >= 0

def test_ai_evaluation_report(auth_headers):
    client = TestClient(app)
    res = client.get("/api/v1/ai/evaluation-report", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "top1_accuracy_percent" in data
    assert "parts_accuracy_percent" in data
    assert data["price_variance_percent"] == 0.0 # Bắt buộc = 0.0%
    assert "average_latency_ms" in data
