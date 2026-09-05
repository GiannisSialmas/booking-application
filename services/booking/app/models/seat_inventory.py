import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SeatStatus(str, enum.Enum):
    AVAILABLE = "available"
    SOLD = "sold"


class SeatInventory(Base):
    """One physical seat for one event, and its current availability.

    This is the row that gets locked/updated during the hold-and-confirm
    flow, since it's where "is this seat still available" is decided.
    """

    __tablename__ = "seat_inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Events are owned by the Catalog service's own database -- this is an
    # opaque foreign identifier, not a local foreign key.
    event_id: Mapped[str] = mapped_column(String(64), index=True)
    seat_label: Mapped[str] = mapped_column(String(16))
    status: Mapped[SeatStatus] = mapped_column(
        Enum(SeatStatus, name="seat_status"), default=SeatStatus.AVAILABLE
    )
    price_cents: Mapped[int] = mapped_column(Integer)
    # No "held" status value: a seat is currently held iff status='available'
    # AND hold_expires_at is in the future -- computed at query time, never
    # stored. This means an expired hold is immediately acquirable again
    # without needing a sweep job to first write status back to 'available'.
    # The hold-acquisition query (see #6) must check both status and this
    # timestamp together; a sweep job (see #10) still exists, but only for
    # side effects (marking the parent Booking expired, emitting an event),
    # not for seat-availability correctness.
    hold_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
