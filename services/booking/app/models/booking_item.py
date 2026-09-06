from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BookingItem(Base):
    """One seat within a booking, and the price actually charged for it.

    A booking can cover multiple seats (e.g. a group buying tickets
    together), so this is the join between a Booking and the specific
    SeatInventory rows it includes.
    """

    __tablename__ = "booking_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), index=True)
    seat_inventory_id: Mapped[int] = mapped_column(
        ForeignKey("seat_inventory.id"), index=True
    )
    # Snapshot of the price actually charged, independent of any later
    # change to seat_inventory.price_cents.
    price_cents: Mapped[int] = mapped_column(Integer)
