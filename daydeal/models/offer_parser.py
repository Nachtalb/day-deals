from datetime import date, datetime, time, timedelta
from typing import TypedDict, get_type_hints

from bs4 import BeautifulSoup
from pydantic import BaseModel, PrivateAttr, validator
from pydantic.fields import ModelField

from daydeal.models.offer import Offer

from .. import drivers

__all__ = ["OfferParser"]


class ExtendedSchedule(TypedDict):
    time: time
    weekday: int


Schedule = time | ExtendedSchedule
PossibleDrivers = (
    drivers.StringDriver
    | drivers.HTMLDriver
    | drivers.FormatDriver
    | drivers.RegexDriver
    | drivers.CastDriver
    | drivers.MathDriver
    | drivers.MoneyDriver
)
Input = float | int | str
DriverInput = list[PossibleDrivers | Input] | PossibleDrivers | Input

DefaultDriver = drivers.HTMLDriver


class OfferParser(BaseModel):
    # HTML object used for data extraction
    _html: BeautifulSoup | None = PrivateAttr(None)

    # Portal name for the retailer
    retailer_name: str
    # Uniq ID for each offer
    offer_id: str
    # URL to scrape
    scrape_url: str
    # ID unique to each sold item
    sale_id: DriverInput | None = None

    # Product title
    title: DriverInput
    # Product summary
    summary: DriverInput
    # Product image
    image: DriverInput
    # URL to the sale offer
    url: DriverInput
    # When the sale starts, eg each day or only each week
    schedule: Schedule
    # Full price before discount
    price_full: DriverInput
    # Discounted price
    price_discount: DriverInput | None = None

    # Rating of the product
    rating: DriverInput | None = None
    # Max rating a product can receive
    rating_top: DriverInput | None = None
    # How much pieces are still available
    available_percentage: DriverInput | None = None
    # How many pieces were available in total
    available_total: DriverInput | None = None
    # How many pieces have already been sold
    available_sold: DriverInput | None = None
    # How many pieces are still left
    available_still: DriverInput | None = None

    @validator("*", pre=True, always=True)
    def set_default_driver(cls, value, field: ModelField):
        if field.type_ == DriverInput or field.type_ == DriverInput | None:
            match value:
                case str():
                    value = drivers.HTMLDriver(query=value)
                case int():
                    value = [
                        drivers.StringDriver(string=str(value)),
                        drivers.CastDriver(type="int"),
                    ]
                case float():
                    value = [
                        drivers.StringDriver(string=str(value)),
                        drivers.CastDriver(type="float"),
                    ]
                case list():
                    value = [cls.set_default_driver(item, field) for item in value]
        return value

    def _evaluate_driver(self, driver: drivers.Driver | list[drivers.Driver], value: Input) -> Input:
        if isinstance(driver, drivers.Driver):
            try:
                return driver.evaluate(self, value)
            except Exception:
                if not driver.ignore_errors:
                    raise
                return ""

        for current_driver in driver:
            try:
                value = current_driver.evaluate(self, value)
            except Exception:
                if not current_driver.ignore_errors:
                    raise
                value = ""
        return value

    def evaluate(self, html: str) -> Offer:
        self._html = BeautifulSoup(html, "html.parser")
        types = get_type_hints(OfferParser)
        for name, value in self:
            if types[name] == DriverInput or types[name] == DriverInput | None and value is not None:
                try:
                    setattr(self, name, self._evaluate_driver(value, ""))
                except Exception:
                    print(f"Affected field: {name} = {value}")
                    raise
        return Offer.parse_obj(self)
