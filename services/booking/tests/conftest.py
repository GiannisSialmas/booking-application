"""Shared test fixtures.

Each test runs inside its own database transaction that's rolled back
afterward -- including any commit() the endpoint under test performs --
using SQLAlchemy's "join a session to an external transaction" pattern
(a SAVEPOINT the app's commit() releases, while the outer transaction
never actually lands). This means tests run against the same database
as local dev (no separate test DB needed) without leaving any trace.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import engine, get_db_session
from app.main import app
from app.models import SeatInventory, SeatStatus, User


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db_session() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session: Session) -> User:
    user = User(email="test@example.com")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_seats(db_session: Session) -> list[SeatInventory]:
    seats = [
        SeatInventory(
            event_id="test-event",
            seat_label=label,
            status=SeatStatus.AVAILABLE,
            price_cents=5000,
        )
        for label in ("A1", "A2", "A3")
    ]
    db_session.add_all(seats)
    db_session.commit()
    for seat in seats:
        db_session.refresh(seat)
    return seats
