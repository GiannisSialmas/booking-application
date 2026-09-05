from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    """A customer who can hold, book, and pay for seats."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 320 = RFC 5321's max email length (64-char local part + '@' + 255-char domain).
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
