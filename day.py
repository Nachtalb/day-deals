from asyncio import as_completed, gather, run
from datetime import date, datetime, timedelta
import json
from pprint import pprint as pp
import re

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from dateutil.parser import isoparse


async def digitec(session: ClientSession):
    url = "https://www.digitec.ch/api/graphql/get-daily-deal-previews"

    payload = json.dumps(
        [
            {
                "operationName": "GET_DAILY_DEAL_PREVIEWS",
                "variables": {"portalIds": [25, 22]},
                "query": (
                    "query GET_DAILY_DEAL_PREVIEWS($portalIds: [Int!]) {\n  dailyDeal {\n    previews(portalIds:"
                    " $portalIds) {\n      portalId\n      product {\n        ...ProductWithOffer\n      }\n    }\n "
                    " }\n}\n\nfragment ProductWithOffer on ProductWithOffer {\n  product {\n   "
                    " ...ProductMandatorIndependent\n  }\n  offer {\n    ...ProductOffer\n  }\n}\n\nfragment"
                    " ProductMandatorIndependent on ProductV2 {\n  id\n  productId\n  name\n  nameProperties\n "
                    " productTypeName\n  brandId\n  brandName\n  averageRating\n  totalRatings\n  images {\n    url\n  "
                    "  height\n    width\n  }\n}\n\nfragment ProductOffer on OfferV2 {\n  id\n  productId\n  price {\n "
                    "   amountIncl\n    currency\n  }\n  volumeDiscountPrices {\n    price {\n      amountIncl\n     "
                    " currency\n    }\n  }\n  salesInformation {\n    numberOfItems\n    numberOfItemsSold\n   "
                    " isEndingSoon\n    validFrom\n  }\n  insteadOfPrice {\n    price {\n      amountIncl\n     "
                    " currency\n    }\n  }\n}"
                ),
            }
        ]
    )

    headers = {
        "Host": "www.digitec.ch",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.120"
            " Safari/537.36"
        ),
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Origin": "https://www.digitec.ch",
        "Accept-Encoding": "gzip, deflate",
    }

    async with session.post(url, headers=headers, data=payload) as response:
        return digitec_data(await response.json())


async def digitec_data(data):
    product_wrappers = data[0]["data"]["dailyDeal"]["previews"]
    for wrapper in product_wrappers:
        product = wrapper["product"]["product"]
        offer = wrapper["product"]["offer"]
        portal = "digitec" if wrapper["portalId"] == 25 else "galaxus"

        info = {
            "id": product["productId"],
            "name": product["name"],
            "brand": product["brandName"],
            "rating": product["averageRating"],
            "rating-top": 5,
            "description": f"{product['productTypeName']}, {product['nameProperties']}",
            "image": product["images"][0]["url"],
            "price-before": offer["insteadOfPrice"]["price"]["amountIncl"],
            "price-after": offer["price"]["amountIncl"],
            "quantity-total": offer["salesInformation"]["numberOfItems"],
            "quantity-sold": offer["salesInformation"]["numberOfItemsSold"],
            "valid-from": isoparse(offer["salesInformation"]["validFrom"]),
            "valid-for": timedelta(days=1),
            "url": f"https://www.{portal}.ch/product/{product['productId']}",
            "portal": portal.title(),
            "currency": "CHF",
            "next-sale-at": datetime.combine(date.today(), datetime.min.time()) + timedelta(days=1),
        }

        info["percent-available"] = (1 - info["quantity-sold"] / info["quantity-total"]) * 100

        yield info


async def brack(session):
    async with session.get("https://daydeal.ch") as response:
        return brack_data(await response.text())


async def brack_data(raw):
    html = BeautifulSoup(raw, "html.parser")

    url = html.find(class_="js-product-button")
    url = url.href if url else "https://daydeal.ch/"

    today = datetime.combine(date.today(), datetime.min.time())
    next_sale_at = today + (timedelta(hours=9) if datetime.now().hour < 9 else timedelta(days=1, hours=9))

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
        "price-before": int(re.sub(r"\D", "", html.find(class_="js-old-price").text)),
        "price-after": int(re.sub(r"\D", "", html.find(class_="js-deal-price").text)),
        "quantity-total": -1,
        "quantity-sold": -1,
        "percent-available": int(re.sub(r"\D", "", html.find(class_="product-progress__availability").text)),
        "valid-from": today,
        "valid-for": timedelta(days=1),
        "portal": "Brack / daydeal.ch",
        "url": url,
        "currency": "CHF",
        "next-sale-at": next_sale_at,
    }

    yield info


async def twenty_min(session):
    async with session.get("https://myshop.20min.ch/de_DE/") as response:
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
        "price-before": int(float(html.find(class_="deal-old-price").find("span").text)),
        "price-after": int(float(html.find(class_="deal-price").text)),
        "quantity-total": -1,
        "percent-available": int(html.find(class_="deal-inventory").text),
        "valid-from": datetime.combine(date.today(), datetime.min.time()),
        "valid-for": timedelta(days=1),
        "portal": "20min",
        "url": "https://myshop.20min.ch" + html.find(class_="deal-link").attrs["href"],
        "currency": "CHF",
        "next-sale-at": datetime.combine(date.today(), datetime.min.time()) + timedelta(days=1),
    }
    info["quantity-sold"] = info["quantity-total"] * (info["percent-available"] / 100)
    yield info


async def send_to_telegram(session, offer):
    print(offer["portal"])
    if offer["quantity-total"] > 0:
        availability = f"Noch {offer['quantity-total'] - offer['quantity-sold']} Stück verfügbar!"
    elif offer["percent-available"] > 0:
        availability = f"Noch {offer['percent-available']}% verfügbar!"
    else:
        hours_to_sale = (offer["next-sale-at"] - datetime.now()).seconds // 60 // 60
        availability = f"Ausverkauft, schau in {hours_to_sale} Stunden wieder nach!"

    text = f"""<b>{offer['portal']}: {offer['name']}</b>
{offer['description']}

{availability}

<s>{offer['price-before']} {offer['currency']}</s> {offer['price-after']} {offer['currency']}
"""

    data = {
        "text": text,
        "chat_id": -1001830374932,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(
            {
                "inline_keyboard": [
                    [
                        {
                            "text": "Zum Angebot ➡️" if offer["percent-available"] > 0 else "Ausverkauft 😔",
                            "url": offer["url"],
                        }
                    ]
                ]
            }
        ),
    }

    async with session.post(
        "https://api.telegram.org/bot5649916237:AAFv6gZZJxDMPV8JZhGBdWdLU3afbtTzBdY/sendMessage", data=data
    ) as response:
        if response.status != 200:
            data = await response.json()
            print(data)


async def main():
    async with ClientSession() as session:
        tasks = [
            digitec(session),
            brack(session),
            twenty_min(session),
        ]

        senders = []

        for result in as_completed(tasks):
            result = await result
            async for offer in result:
                senders.append(send_to_telegram(session, offer))

        [await result for result in as_completed(senders)]


run(main())
