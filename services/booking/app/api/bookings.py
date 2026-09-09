from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db_session
from app.models import Booking, BookingItem, BookingStatus, SeatInventory, SeatStatus, User
from app.schemas.booking import HeldSeat, HoldRequest, HoldResponse

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/hold", response_model=HoldResponse, status_code=status.HTTP_201_CREATED)
def hold_seats(payload: HoldRequest, db: Session = Depends(get_db_session)) -> HoldResponse:
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    settings = get_settings()
    new_expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.hold_duration_minutes)

    # Single atomic UPDATE: a row matches only if it's genuinely acquirable
    # right now, regardless of whether an earlier hold on it was ever
    # explicitly released -- see the comment on SeatInventory.hold_expires_at.
    acquire_stmt = (
        update(SeatInventory)
        .where(
            SeatInventory.id.in_(payload.seat_ids),
            SeatInventory.status == SeatStatus.AVAILABLE,
            or_(
                SeatInventory.hold_expires_at.is_(None),
                SeatInventory.hold_expires_at < datetime.now(timezone.utc),
            ),
        )
        .values(hold_expires_at=new_expiry)
        .returning(
            SeatInventory.id,
            SeatInventory.event_id,
            SeatInventory.seat_label,
            SeatInventory.price_cents,
        )
    )
    acquired = db.execute(acquire_stmt).all()

    acquired_ids = {row.id for row in acquired}
    missing_ids = set(payload.seat_ids) - acquired_ids
    if missing_ids:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seat(s) not available: {sorted(missing_ids)}",
        )

    event_ids = {row.event_id for row in acquired}
    if len(event_ids) > 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All seats in one booking must belong to the same event",
        )

    booking = Booking(user_id=user.id, status=BookingStatus.HELD)
    db.add(booking)
    db.flush()  # assigns booking.id without committing yet

    items = [
        BookingItem(
            booking_id=booking.id,
            seat_inventory_id=row.id,
            price_cents=row.price_cents,
        )
        for row in acquired
    ]
    db.add_all(items)
    db.commit()

    return HoldResponse(
        id=booking.id,
        status=booking.status.value,
        hold_expires_at=new_expiry,
        items=[
            HeldSeat(
                seat_inventory_id=row.id,
                seat_label=row.seat_label,
                price_cents=row.price_cents,
            )
            for row in acquired
        ],
    )
