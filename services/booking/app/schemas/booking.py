from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class HoldRequest(BaseModel):
    user_id: int
    seat_ids: list[int] = Field(min_length=1)

    @field_validator("seat_ids")
    @classmethod
    def no_duplicate_seats(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("seat_ids must not contain duplicates")
        return value


class HeldSeat(BaseModel):
    seat_inventory_id: int
    seat_label: str
    price_cents: int


class HoldResponse(BaseModel):
    id: int
    status: str
    hold_expires_at: datetime
    items: list[HeldSeat]
