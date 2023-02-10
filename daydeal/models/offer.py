from datetime import datetime, time, timedelta
from hashlib import sha1
from typing import TypedDict

from pydantic import BaseModel, root_validator, validator
from pydantic.fields import ModelField

__all__ = ["Offer"]


class ExtendedSchedule(TypedDict):
    time: time
    weekday: int


Schedule = time | ExtendedSchedule


class Offer(BaseModel):
    # Portal name for the retailer
    retailer_name: str
    # Uniq ID for each offer
    offer_id: str
    # URL to scrape
    scrape_url: str

    # Product title
    title: str
    # Product summary
    summary: str
    # Product image
    image: str
    # URL to the sale offer
    url: str
    # When the sale starts, eg each day or only each week
    schedule: Schedule
    # Full price before discount
    price_full: str
    # Discounted price
    price_discount: str | None = None

    # Rating of the product
    rating: int | None = None
    # Max rating a product can receive
    rating_top: int | None = None
    # How much pieces are still available
    available_percentage: int | None = None
    # How many pieces were available in total
    available_total: int | None = None
    # How many pieces have already been sold
    available_sold: int | None = None
    # How many pieces are still left
    available_still: int | None = None

    # When the current sale started
    scheduled_current: datetime | None = None
    # When the next sale starts
    scheduled_next: datetime | None = None
    # ID of the current sale
    sale_id: str | None = None

    @validator("*", pre=True, always=True)
    def set_default_driver(cls, value, field: ModelField):
        if value is not None:
            match field.type_:
                case t if t == int | None and not isinstance(value, int):
                    value = int(value)
                case t if t == str | None and not isinstance(value, str):
                    value = str(value)
                case t if t == str and not isinstance(value, str):
                    value = str(value)
        return value

    @root_validator
    def fill_defaults(cls, values: dict) -> dict:
        if (
            (values["available_total"] and values["available_total"] == values["available_sold"])
            or values["available_still"] == 0
            or values["available_percentage"] == 0
        ):
            values["available_still"] = 0
            values["available_percentage"] = 0

        current, next = Offer.schedules(values["schedule"])
        if values["scheduled_current"] is None:
            values["scheduled_current"] = current
        if values["scheduled_next"] is None:
            values["scheduled_next"] = next

        if values["sale_id"] is None:
            values["sale_id"] = sha1(
                string=(
                    values["name"] + values["summary"] + (values["price_discount"] or values["price_full"]).encode()
                )
            ).hexdigest()

        return values

    @staticmethod
    def schedules(schedule: Schedule) -> tuple[datetime, datetime]:
        """Get current and next sale date"""
        now = datetime.now()

        if isinstance(schedule, dict):
            # ==> scheduled Tu 0900 <==
            # now Tu 0800  ==> Tu - (now.weekday 1 - 1 scheduled_weekday) = Tu & 0900 scheduled.time = Tu 0900 = schedule_date
            # now We 1000  ==> We - (now.weekday 2 - 1 scheduled.weekday) = Tu & 0900 scheduled.time = Tu 0900 = schedule_date
            # next_schedule if now < schedule_date else current_schedule

            schedule_date = datetime.combine(
                # (now -               now.weekday   - schedule           )  & scheduled.time
                (now - timedelta(days=now.weekday() - schedule["weekday"])),
                schedule["time"],
            )

            if now < schedule_date:
                next_schedule = schedule_date
                current_schedule = schedule_date - timedelta(days=7)
            else:
                next_schedule = schedule_date + timedelta(days=7)
                current_schedule = schedule_date
        else:
            # ==> scheduled 0900 <==
            # now Tu 0300  ==> now & scheduled = schedule_date
            # now Tu 1000  ==> now & scheduled = schedule_date
            # next_schedule if now.time < schedule_date.time and now.date == schedule_date.date else current_schedule

            #                                now & scheduled
            schedule_date = datetime.combine(now, schedule)
            if now.time() < schedule_date.time() and now.date() == schedule_date.date():
                next_schedule = schedule_date
                current_schedule = schedule_date - timedelta(days=1)
            else:
                next_schedule = schedule_date + timedelta(days=1)
                current_schedule = schedule_date

        return current_schedule, next_schedule
