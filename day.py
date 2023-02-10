from asyncio import as_completed, run
from datetime import date, datetime, timedelta
from pathlib import Path
import re

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from jsondatetime import jsondatetime as json


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
            "description": f"{product['productTypeName']}, {product['nameProperties']}".strip(" ,"),
            "image": product["images"][0]["url"],
            "price_before": offer["insteadOfPrice"]["price"]["amountIncl"] if offer["insteadOfPrice"] else None,
            "price_after": offer["price"]["amountIncl"],
            "quantity_total": offer["salesInformation"]["numberOfItems"],
            "quantity_sold": offer["salesInformation"]["numberOfItemsSold"],
            "url": f"https://www.{portal}.ch/product/{product['productId']}",
            "portal": portal.title(),
            "currency": "CHF",
            "next_sale_at": datetime.combine(date.today(), datetime.min.time()) + timedelta(days=1),
        }

        info["percent_available"] = (1 - info["quantity_sold"] / info["quantity_total"]) * 100

        yield info


async def brack(session, day=True):
    url = "https://daydeal.ch/"
    if not day:
        url += "deal-of-the-week"
    async with session.get(url) as response:
        return brack_data(await response.text(), day, url)


async def brack_data(raw, day, url):
    html = BeautifulSoup(raw, "html.parser")

    today = datetime.combine(date.today(), datetime.min.time())
    now = datetime.now()
    if day:
        portal = "Brack / daydeal.ch Tagesangebot"
        next_sale_at = today + timedelta(hours=9)
        next_sale_at = next_sale_at if now.hour < 9 else (next_sale_at + timedelta(days=1))
        current_id = (next_sale_at - timedelta(days=1)).strftime("%d%m%Y")
    else:
        portal = "Brack / daydeal.ch Wochenangebot"
        next_sale_at = today + timedelta(days=7 - today.weekday(), hours=9)
        next_sale_at = next_sale_at - timedelta(days=7) if today.weekday() == 0 and now.hour < 9 else next_sale_at
        current_id = (next_sale_at - timedelta(days=7)).strftime("%d%m%Y")

    info = {
        "name": html.find(class_="product-description__title1").text,
        "brand": "",
        "id": current_id,
        "rating": -1,
        "rating_top": -1,
        "description": html.find(class_="product-description__title2").text,
        "image": html.find(class_="product-tabs__img").attrs["src"],
        "price_before": float(re.search(r"\d+(\.\d+)?", html.find(class_="js-old-price").text).group()),
        "price_after": float(re.search(r"\d+(\.\d+)?", html.find(class_="js-deal-price").text).group()),
        "quantity_total": -1,
        "quantity_sold": -1,
        "percent_available": int(re.sub(r"\D", "", html.find(class_="product-progress__availability").text)),
        "portal": portal,
        "url": url,
        "currency": "CHF",
        "next_sale_at": next_sale_at,
    }

    yield info


async def twenty_min(session, day=True):
    if day:
        path = "angebot-des-tages"
    else:
        path = "wochenangebot"
    async with session.get(f"https://myshop.20min.ch/de_DE/category/{path}") as response:
        return twenty_min_data(await response.text(), day)


async def twenty_min_data(raw, day=True):
    today = datetime.combine(date.today(), datetime.min.time())
    if day:
        portal = "20min Tagesangebot"
        next_sale_at = today + timedelta(days=1)
        current_id = today.strftime("%d%m%Y")
    else:
        portal = "20min Wochenangebot"
        next_sale_at = today + timedelta(days=7 - today.weekday())
        current_id = (next_sale_at - timedelta(days=7)).strftime("%d%m%Y")

    html = BeautifulSoup(raw, "html.parser")

    info = {
        "name": html.find(class_="deal-title").text,
        "brand": "",
        "id": current_id,
        "rating": -1,
        "rating_top": -1,
        "description": html.find(class_="deal-subtitle").text.strip(),
        "image": html.find(class_="deal-img").find("img").attrs["data-src"],
        "price_before": float(html.find(class_="deal-old-price").find("span").text),
        "price_after": float(html.find(class_="deal-price").text),
        "quantity_total": -1,
        "percent_available": int(html.find(class_="deal-inventory").text),
        "portal": portal,
        "url": "https://myshop.20min.ch" + html.find(class_="deal-link").attrs["href"],
        "currency": "CHF",
        "next_sale_at": next_sale_at,
    }
    info["quantity_sold"] = info["quantity_total"] * (info["percent_available"] / 100)
    yield info


def get_availability(offer):
    if offer["quantity_total"] > 0 and offer["quantity_sold"] != offer["quantity_total"]:
        percentage = (offer["quantity_total"] - offer["quantity_sold"]) / offer["quantity_total"] * 100
        availability = (
            f"Noch {offer['quantity_total'] - offer['quantity_sold']}/{offer['quantity_total']} Stück verfügbar!"
        )
    elif offer["percent_available"] > 0:
        percentage = offer["percent_available"]
        availability = f"Noch {offer['percent_available']}% verfügbar!"
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

    return f"{level} - {availability}"


def clean_money(money: int | float | None) -> str | None:
    """Unify money representation

    None   => None
    i10    => "10"
    f22.00 => "22"
    f22.90 => "22.90"
    """
    if money is None:
        return
    if isinstance(money, float) and int(money) == money:
        money = int(money)
    if isinstance(money, float):
        return f"{money:.2f}"
    return str(money)


def create_or_update_sale(offer):
    portal = offer["portal"]
    availability = get_availability(offer)

    if offer["rating"] > 0:
        rating = round(offer["rating"]) * "★" + ((offer["rating_top"] - round(offer["rating"])) * "☆")
    else:
        rating = ""

    price_before = clean_money(offer["price_before"])
    price_after = clean_money(offer["price_after"])

    if not price_before:
        price = f"{price_after} {offer['currency']}"
    else:
        price = f"<s>{price_before} {offer['currency']}</s> {price_after} {offer['currency']}"

    text = f"""<b>{portal}: {offer['name']} {rating}</b>
{offer['description']}

{availability}

{price}

<a href="{offer['image']}">​</a>
"""

    payload = {
        "text": text,
        "chat_id": CONFIG["chat_id"],
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

    if TODAYS_IDS[portal].get("id") != offer["id"]:
        method = "sendMessage"
        message = f"🟢 {portal} - New Deal"
    elif TODAYS_IDS[portal].get("msg") == payload:
        print(f"🟡 {portal} - Nothing changed")
        return
    else:
        method = "editMessageText"
        payload["message_id"] = TODAYS_IDS[portal]["mid"]
        message = f"🔵 {portal} - Updated Deal"

    return {
        "update_id": True,
        "method": method,
        "log": message,
        "payload": payload,
        "portal": offer["portal"],
        "id": offer["id"],
        "offer": offer,
    }


def update_obsolete_sale(old_data: dict | None, next_sale_link: str | None):
    if not old_data:
        return
    offer = old_data["offer"]

    if next_sale_link:
        availability = f'🔴 Das Angebot ist vorbei, <a href="{next_sale_link}">schau dir das nächste an!</a>'
    else:
        availability = "🔴 Das Angebot ist vorbei, schau dir das nächste an!"

    if offer["rating"] > 0:
        rating = round(offer["rating"]) * "★" + ((offer["rating_top"] - round(offer["rating"])) * "☆")
    else:
        rating = ""

    text = f"""<b>{offer['portal']}: {offer['name']} {rating}</b>
{offer['description']}
<a href="{offer['image']}">​</a>
{availability}

<s>{offer['price_before']} {offer['currency']}</s> {offer['price_after']} {offer['currency']}
"""

    payload = {
        "text": text,
        "chat_id": CONFIG["chat_id"],
        "parse_mode": "HTML",
        "reply_markup": json.dumps(
            {
                "inline_keyboard": [
                    [
                        {
                            "text": "Angebor vorbei",
                            "url": offer["url"],
                        }
                    ]
                ]
            }
        ),
    }

    method = "editMessageText"
    payload["message_id"] = old_data["mid"]
    message = f"🔴 {offer['portal']} - Sale ended"

    return {
        "update_id": False,
        "method": method,
        "log": message,
        "payload": payload,
        "portal": offer["portal"],
        "id": offer["id"],
        "offer": offer,
    }


def get_message_link(message: dict) -> str | None:
    if message["chat"]["type"] not in ["private", "group"]:
        if username := message["chat"].get("username"):
            to_link = username
        else:
            # Get rid of leading -100 for supergroups
            to_link = f"c/{str(message['chat']['id'])[4:]}"
        return f"https://t.me/{to_link}/{message['message_id']}"
    return


async def prepare_and_send_to_telegram(session, offer):
    old_data = TODAYS_IDS.get(offer["portal"])
    is_new = old_data and old_data.get("id") != offer["id"]
    message = None

    if task := create_or_update_sale(offer):
        message = await send_to_telegram(session, task)

    if message and is_new and (task := update_obsolete_sale(old_data, get_message_link(message))):
        await send_to_telegram(session, task)


async def send_to_telegram(session, task) -> dict | None:
    async with session.post(
        f"https://api.telegram.org/bot{CONFIG['token']}/{task['method']}",
        data=task["payload"],
    ) as response:
        data = await response.json()
        print(task["log"])
        if data["ok"] and task["update_id"]:
            TODAYS_IDS[task["portal"]] = {
                "id": task["id"],
                "mid": data["result"]["message_id"],
                "msg": task["payload"],
                "offer": task["offer"],
            }
        elif not data["ok"] and "message is not modified" not in data.get("description", ""):
            print(f"{data=}\n{task=}")
    return data.get("result")


async def main():
    async with ClientSession() as session:
        tasks = [
            digitec(session),
            brack(session),
            brack(session, day=False),  # Wochenangebot
            twenty_min(session),
            twenty_min(session, day=False),  # Wochenangebot
        ]

        senders = []

        for result in as_completed(tasks):
            result = await result
            async for offer in result:
                TODAYS_IDS.setdefault(offer["portal"], {})
                senders.append(prepare_and_send_to_telegram(session, offer))

        [await result for result in as_completed(senders)]


path = Path(__file__).with_name("todays_ids.json")
path.touch()

config_path = Path(__file__).with_name("config.json")
CONFIG: dict = json.loads(config_path.read_text())

TODAYS_IDS: dict = json.loads(path.read_text().strip() or "{}")

run(main())

path.write_text(json.dumps(TODAYS_IDS, ensure_ascii=False, cls=json.DatetimeJSONEncoder, indent=4, sort_keys=True))
