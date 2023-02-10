import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, validator

from .safe_math import eval_expr as safe_math

if TYPE_CHECKING:
    from .models import OfferParser


Input = str | float | int


class Driver(BaseModel):
    driver: str
    ignore_errors: bool = False
    debugger: bool = False

    def evaluate(self, offer: "OfferParser", input: Input) -> Input:
        if self.debugger:
            try:
                __import__("ipdb").set_trace()
            except ImportError:
                __import__("pdb").set_trace()


class StringDriver(Driver):
    driver: str = "string"
    # Static string
    string: str

    def evaluate(self, offer: "OfferParser", input: Input) -> Input:
        """Return given string"""
        super().evaluate(offer, input)
        return self.string


class HTMLDriver(Driver):
    driver: str = "html"
    # CSS query
    query: str
    # Attribute to return instead of text content
    attribute: str | None = None

    def evaluate(self, offer: "OfferParser", input: Input) -> Input:
        """Evaluate query"""
        super().evaluate(offer, input)
        element = offer._html.select_one(self.query)
        if not element:
            raise ValueError(f'HTMLDriver: No results to query "{self.query}"')
        if self.attribute:
            return element.attrs[self.attribute]
        return element.text


class FormatDriver(Driver):
    driver: str = "format"
    # f-string template
    format: str

    def evaluate(self, offer: "OfferParser", input: Input) -> Input:
        """Format string with python f-strings"""
        super().evaluate(offer, input)
        input = str(input)
        return self.format.format(**offer.dict())


class RegexDriver(Driver):
    driver: str = "regex"
    # Extraction regex
    regex: str
    # Join extracted groups is not None, stronger than group_index
    join_groups: str | None = None
    # Either use "findall" or "search" to extract data
    method: str = "findall"
    # Get element at given index, uses .group() if method search is used
    group_index: int = 0

    def evaluate(self, offer: "OfferParser", input: Input) -> Input:
        """Extract data from input via regex"""
        super().evaluate(offer, input)
        input = str(input)
        reg = re.compile(self.regex)
        match: re.Match | list[str] | None = None
        if self.method == "findall":
            match = reg.findall(input)
        else:
            match = reg.search(input)

        if match is None:
            raise ValueError("Could not extract data with given regex")

        if self.join_groups is not None:
            return self.join_groups.join(match if isinstance(match, list) else match.groups())
        return match[self.group_index] if isinstance(match, list) else match.group(self.group_index)


class CastDriver(Driver):
    driver: str = "cast"
    # Type to be cast into, either float, int or str
    type: str

    @validator("type")
    def allowed_types(cls, value):
        if value not in ["float", "str", "int"]:
            raise ValueError('Type has to be either "float", "int" or "str"')
        return value

    def evaluate(self, offer: "OfferParser", input: Input) -> Input:
        """Cast the input to either float, int or str"""
        super().evaluate(offer, input)
        match self.type:
            case "float":
                return float(input)
            case "int":
                return int(input)
            case _:
                return str(input)


class MathDriver(Driver):
    driver: str = "math"
    # Math equation, supports math on strings eg. '"a" * 4' = "aaaa"
    equation: str

    def evaluate(self, offer: "OfferParser", input: Input) -> Input:
        """Evaluate a given math expression"""
        super().evaluate(offer, input)
        if isinstance(input, str):
            input = f'"{input}"'  # allows for '"a" * 4' => 'aaaa'
        return safe_math(self.equation.format(input=input))


class MoneyDriver(Driver):
    driver: str = "money"
    # Currency short, eg. $ or USD
    currency: str
    # Should the 10.00 be shortened to 10 or should it stay 10.00
    shorten: bool = True
    # Prepend or append the currency, eg. "£40.00" vs "40.00 $"
    prepend_currency: bool = False

    def evaluate(self, offer: "OfferParser", input: Input) -> Input:
        """Formats an input into a money string"""
        super().evaluate(offer, input)
        input = float(input)

        if self.shorten and input == int(input):
            input = int(input)

        return f"{self.currency}{input}" if self.prepend_currency else f"{input} {self.currency}"
