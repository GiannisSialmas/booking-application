"""Seeds a sample user and one event's seat map, for local dev/testing.

Manual, local-dev-only tool -- deliberately not wired into
docker-entrypoint.sh alongside migrations. Idempotent: safe to run more
than once, it skips whatever already exists.

Run via: docker compose exec booking python -m scripts.seed
"""

from app.core.database import SessionFactory
from app.models import SeatInventory, SeatStatus, User

SAMPLE_EVENT_ID = "sample-event-1"
SAMPLE_USER_EMAIL = "demo@example.com"

ROWS = ["A", "B", "C", "D", "E"]
SEATS_PER_ROW = 10
PRICE_CENTS_BY_ROW = {
    "A": 10000,
    "B": 10000,
    "C": 7500,
    "D": 7500,
    "E": 5000,
}


def seed_user(db) -> None:
    existing = db.query(User).filter_by(email=SAMPLE_USER_EMAIL).first()
    if existing is not None:
        print(f"User {SAMPLE_USER_EMAIL!r} already exists (id={existing.id}), skipping.")
        return

    user = User(email=SAMPLE_USER_EMAIL)
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Seeded user {SAMPLE_USER_EMAIL!r} (id={user.id}).")


def seed_seats(db) -> None:
    existing = db.query(SeatInventory).filter_by(event_id=SAMPLE_EVENT_ID).first()
    if existing is not None:
        print(f"Seats for event {SAMPLE_EVENT_ID!r} already exist, skipping.")
        return

    seats = [
        SeatInventory(
            event_id=SAMPLE_EVENT_ID,
            seat_label=f"{row}{number}",
            status=SeatStatus.AVAILABLE,
            price_cents=PRICE_CENTS_BY_ROW[row],
        )
        for row in ROWS
        for number in range(1, SEATS_PER_ROW + 1)
    ]
    db.add_all(seats)
    db.commit()
    print(f"Seeded {len(seats)} seats for event {SAMPLE_EVENT_ID!r}.")


def seed() -> None:
    db = SessionFactory()
    try:
        seed_user(db)
        seed_seats(db)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
