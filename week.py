from asyncio import as_completed, run
from datetime import date, datetime, timedelta
import json
from pprint import pprint as pp
import re

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from dateutil.parser import isoparse


async def brack(session):
    async with session.get("https://daydeal.ch/deal-of-the-week") as response:
        return brack_data(await response.text())


async def brack_data(raw):
    html = BeautifulSoup(raw, "html.parser")

    url = html.find(class_="js-product-button")
    url = url.href if url else ""

    info = {
        "name": html.find(class_="product-description__title1").text,
        "brand": "",
        "id": -1,
        "rating": -1,
        "rating-top": -1,
        "description": (
            html.find(class_="product-description__title2").text
            + "\n"
            + html.find(class_="product-description__list").text.strip()
        ),
        "image": html.find(class_="product-tabs__img").src,
        "price-before": re.sub(r"\D", "", html.find(class_="js-old-price").text),
        "price-after": re.sub(r"\D", "", html.find(class_="js-deal-price").text),
        "quantity-total": -1,
        "quantity-sold": -1,
        "percent-available": re.sub(r"\D", "", html.find(class_="product-progress__availability").text),
        "valid-from": datetime.combine(date.today(), datetime.min.time()),
        "valid-for": timedelta(days=1),
        "portal": "Brack / daydeal.ch",
        "url": url,
        "currency": "CHF",
    }

    yield info


async def twenty_min(session):
    async with session.get("https://myshop.20min.ch/de_DE/category/wochenangebot") as response:
        return twenty_min_data(await response.text())


async def twenty_min_data(raw):
    html = BeautifulSoup(raw, "html.parser")

    info = {
        "name": html.find(class_="deal-title").text,
        "brand": "",
        "id": -1,
        "rating": -1,
        "rating-top": -1,
        "description": html.find(class_="deal-subtitle").text.strip(),
        "image": html.find(class_="deal-img").find("img").attrs["data-src"],
        "price-before": float(html.find(class_="deal-old-price").find("span").text),
        "price-after": float(html.find(class_="deal-price").text),
        "quantity-total": int(re.sub(r"\D", "", html.find(class_="deal-products-quantity").text)),
        "percent-available": int(html.find(class_="deal-inventory").text),
        "valid-from": datetime.combine(date.today(), datetime.min.time()),
        "valid-for": timedelta(days=1),
        "portal": "20min",
        "url": "https://myshop.20min.ch" + html.find(class_="deal-link").attrs["href"],
        "currency": "CHF",
    }
    info["quantity-sold"] = info["quantity-total"] * (info["percent-available"] / 100)
    yield info


async def main():
    async with ClientSession() as session:
        tasks = [
            brack(session),
            twenty_min(session),
        ]

        for result in as_completed(tasks):
            result = await result
            async for offer in result:
                pp(offer)


run(main())
