from asyncio import as_completed, run
from datetime import date, datetime, timedelta
import json
from pathlib import Path
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
            "rating_top": 5,
            "description": f"{product['productTypeName']}, {product['nameProperties']}",
            "image": product["images"][0]["url"],
            "price_before": offer["insteadOfPrice"]["price"]["amountIncl"],
            "price_after": offer["price"]["amountIncl"],
            "quantity_total": offer["salesInformation"]["numberOfItems"],
            "quantity_sold": offer["salesInformation"]["numberOfItemsSold"],
            "valid_from": isoparse(offer["salesInformation"]["validFrom"]),
            "valid_for": timedelta(days=1),
            "url": f"https://www.{portal}.ch/product/{product['productId']}",
            "portal": portal.title(),
            "currency": "CHF",
            "next_sale_at": datetime.combine(date.today(), datetime.min.time()) + timedelta(days=1),
        }

        info["percent_available"] = (1 - info["quantity_sold"] / info["quantity_total"]) * 100

        yield info


async def brack(session):
    async with session.get("https://daydeal.ch") as response:
        return brack_data(await response.text())


async def brack_data(raw):
    html = BeautifulSoup(raw, "html.parser")

    url = html.find(class_="js-product-button")
    url = html.find(class_="product-pricing__buy")
    url = url.attrs["href"] if url else "https://daydeal.ch/"

    today = datetime.combine(date.today(), datetime.min.time())
    today_deal_time = today + timedelta(hours=9)

    if datetime.now().hour > 9:
        next_sale_at = today_deal_time + timedelta(days=1)
        current_id = today.strftime("%d%m%Y")
    else:
        next_sale_at = today_deal_time
        current_id = (today + timedelta(days=-1)).strftime("%d%m%Y")

    info = {
        "name": html.find(class_="product-description__title1").text,
        "brand": "",
        "id": current_id,
        "rating": -1,
        "rating_top": -1,
        "description": (
            html.find(class_="product-description__title2").text
            + "\n"
            + html.find(class_="product-description__list").text.strip()
        ),
        "image": html.find(class_="product-tabs__img").attrs["src"],
        "price_before": int(re.sub(r"\D", "", html.find(class_="js-old-price").text)),
        "price_after": int(re.sub(r"\D", "", html.find(class_="js-deal-price").text)),
        "quantity_total": -1,
        "quantity_sold": -1,
        "percent_available": int(re.sub(r"\D", "", html.find(class_="product-progress__availability").text)),
        "valid_from": today,
        "valid_for": timedelta(days=1),
        "portal": "Brack / daydeal.ch",
        "url": url,
        "currency": "CHF",
        "next_sale_at": next_sale_at,
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
        "id": date.today().strftime("%d%m%Y"),
        "rating": -1,
        "rating_top": -1,
        "description": html.find(class_="deal-subtitle").text.strip(),
        "image": html.find(class_="deal-img").find("img").attrs["data-src"],
        "price_before": int(float(html.find(class_="deal-old-price").find("span").text)),
        "price_after": int(float(html.find(class_="deal-price").text)),
        "quantity_total": -1,
        "percent_available": int(html.find(class_="deal-inventory").text),
        "valid_from": datetime.combine(date.today(), datetime.min.time()),
        "valid_for": timedelta(days=1),
        "portal": "20min",
        "url": "https://myshop.20min.ch" + html.find(class_="deal-link").attrs["href"],
        "currency": "CHF",
        "next_sale_at": datetime.combine(date.today(), datetime.min.time()) + timedelta(days=1),
    }
    info["quantity_sold"] = info["quantity_total"] * (info["percent_available"] / 100)
    yield info


async def send_to_telegram(session, offer):
    if offer["quantity_total"] > 0:
        percentage = (offer["quantity_total"] - offer["quantity_sold"]) / offer["quantity_total"] * 100
        availability = (
            f"Noch {offer['quantity_total'] - offer['quantity_sold']}/{offer['quantity_total']} St├╝ck verf├╝gbar!"
        )
    elif offer["percent_available"] > 0:
        percentage = offer["percent_available"]
        availability = f"Noch {offer['percent_available']}% verf├╝gbar!"
    else:
        hours_to_sale = (offer["next_sale_at"] - datetime.now()).seconds // 60 // 60
        percentage = 0
        availability = f"Ausverkauft! Schau in {hours_to_sale} Stunden wieder nach!"

    if percentage > 50:
        level = "🟢"
    elif percentage > 30:
        level = "🔵"
    elif percentage > 15:
        level = "🟡"
    elif percentage > 0:
        level = "🟠"
    else:
        level = "🔴"

    availability = f"{level} - {availability}"

    if offer["rating"] > 0:
        rating = round(offer["rating"]) * "★" + ((offer["rating_top"] - round(offer["rating"])) * "☆")
    else:
        rating = ""

    text = f"""<b>{offer['portal']}: {offer['name']} {rating}</b>
{offer['description']}

{availability}

<s>{offer['price_before']} {offer['currency']}</s> {offer['price_after']} {offer['currency']}

<a href="{offer['image']}">​</a>
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
                            "text": "Zum Angebot ➡️" if offer["percent_available"] > 0 else "Ausverkauft 😔",
                            "url": offer["url"],
                        }
                    ]
                ]
            }
        ),
    }

    if TODAYS_IDS[offer["portal"]].get("id") != offer["id"]:
        method = "sendMessage"
        print(f"🟢 {offer['portal']} - New Deal")
    else:
        method = "editMessageText"
        data["message_id"] = TODAYS_IDS[offer["portal"]]["mid"]
        print(f"🔵 {offer['portal']} - Updated Deal")

    async with session.post(
        f"https://api.telegram.org/bot5649916237:AAFv6gZZJxDMPV8JZhGBdWdLU3afbtTzBdY/{method}", data=data
    ) as response:
        data = await response.json()
        if data["ok"]:
            TODAYS_IDS[offer["portal"]] = {"id": offer["id"], "mid": data["result"]["message_id"]}


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
                TODAYS_IDS.setdefault(offer["portal"], {})
                senders.append(send_to_telegram(session, offer))

        [await result for result in as_completed(senders)]


path = Path(__file__).with_name("todays_ids.json")
path.touch()

TODAYS_IDS: dict = json.loads((path.read_text().strip() or "{}"))

run(main())

path.write_text(json.dumps(TODAYS_IDS))
