import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SeatStatus(str, enum.Enum):
    AVAILABLE = "available"
    HELD = "held"
    SOLD = "sold"


class SeatInventory(Base):
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
    hold_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
