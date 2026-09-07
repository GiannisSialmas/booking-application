"""Seeds one sample event's seat map into seat_inventory, for local dev/testing.

Manual, local-dev-only tool -- deliberately not wired into
docker-entrypoint.sh alongside migrations. Idempotent: safe to run more
than once, it skips if the sample event's seats already exist.

Run via: docker compose exec booking python -m app.seed
"""

from app.core.database import SessionFactory
from app.models import SeatInventory, SeatStatus

SAMPLE_EVENT_ID = "sample-event-1"

ROWS = ["A", "B", "C", "D", "E"]
SEATS_PER_ROW = 10
PRICE_CENTS_BY_ROW = {
    "A": 10000,
    "B": 10000,
    "C": 7500,
    "D": 7500,
    "E": 5000,
}


def seed() -> None:
    db = SessionFactory()
    try:
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
    finally:
        db.close()


if __name__ == "__main__":
    seed()
