import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, UserRole, Customer, Vehicle, Service, Part
from backend.app.auth import get_password_hash, create_access_token

# In-memory SQLite DB for fast test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Seed minimum users
    manager = User(
        username="admin_test",
        email="admin_test@garage.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Test Manager",
        role=UserRole.MANAGER
    )
    receptionist = User(
        username="reception_test",
        email="reception_test@garage.com",
        hashed_password=get_password_hash("letan123"),
        full_name="Test Receptionist",
        role=UserRole.RECEPTIONIST
    )
    cashier = User(
        username="cashier_test",
        email="cashier_test@garage.com",
        hashed_password=get_password_hash("cashier123"),
        full_name="Test Cashier",
        role=UserRole.CASHIER
    )
    session.add_all([manager, receptionist, cashier])
    session.commit()

    # Seed test customer & vehicle
    customer = Customer(full_name="Test Customer", phone="0999888777", email="test@customer.com")
    session.add(customer)
    session.commit()

    vehicle = Vehicle(
        license_plate="99A-999.99",
        brand="Toyota",
        model="Camry",
        year=2022,
        customer_id=customer.id
    )
    session.add(vehicle)
    session.commit()

    # Seed test service & part
    service = Service(code="SER-TEST", name="Test Service", labor_cost=100000.0)
    part = Part(code="PAR-TEST", name="Test Part", unit_price=500000.0, stock_quantity=10)
    session.add_all([service, part])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def auth_headers(db_session):
    token = create_access_token({"sub": "admin_test", "role": "manager"})
    return {"Authorization": f"Bearer {token}"}
