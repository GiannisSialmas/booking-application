from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import SeatInventory, User


def test_hold_single_seat_success(
    client: TestClient, sample_user: User, sample_seats: list[SeatInventory]
) -> None:
    response = client.post(
        "/bookings/hold",
        json={"user_id": sample_user.id, "seat_ids": [sample_seats[0].id]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "held"
    assert body["items"] == [
        {
            "seat_inventory_id": sample_seats[0].id,
            "seat_label": "A1",
            "price_cents": 5000,
        }
    ]


def test_hold_already_held_seat_conflicts(
    client: TestClient, sample_user: User, sample_seats: list[SeatInventory]
) -> None:
    seat_id = sample_seats[0].id
    first = client.post("/bookings/hold", json={"user_id": sample_user.id, "seat_ids": [seat_id]})
    assert first.status_code == 201

    second = client.post("/bookings/hold", json={"user_id": sample_user.id, "seat_ids": [seat_id]})

    assert second.status_code == 409
    assert str(seat_id) in second.json()["detail"]


def test_hold_partial_mix_rolls_back(
    client: TestClient,
    db_session: Session,
    sample_user: User,
    sample_seats: list[SeatInventory],
) -> None:
    held_seat, free_seat = sample_seats[0], sample_seats[1]
    first = client.post("/bookings/hold", json={"user_id": sample_user.id, "seat_ids": [held_seat.id]})
    assert first.status_code == 201

    mixed = client.post(
        "/bookings/hold",
        json={"user_id": sample_user.id, "seat_ids": [free_seat.id, held_seat.id]},
    )
    assert mixed.status_code == 409

    db_session.refresh(free_seat)
    assert free_seat.hold_expires_at is None


def test_hold_multiple_seats_success(
    client: TestClient, sample_user: User, sample_seats: list[SeatInventory]
) -> None:
    response = client.post(
        "/bookings/hold",
        json={"user_id": sample_user.id, "seat_ids": [sample_seats[1].id, sample_seats[2].id]},
    )

    assert response.status_code == 201
    assert len(response.json()["items"]) == 2


def test_hold_nonexistent_user_returns_404(
    client: TestClient, sample_seats: list[SeatInventory]
) -> None:
    response = client.post(
        "/bookings/hold",
        json={"user_id": 999_999, "seat_ids": [sample_seats[0].id]},
    )

    assert response.status_code == 404


def test_hold_duplicate_seat_ids_rejected(
    client: TestClient, sample_user: User, sample_seats: list[SeatInventory]
) -> None:
    response = client.post(
        "/bookings/hold",
        json={"user_id": sample_user.id, "seat_ids": [sample_seats[0].id, sample_seats[0].id]},
    )

    assert response.status_code == 422
