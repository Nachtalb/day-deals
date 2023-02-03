from asyncio import as_completed, run
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
                #  "query": (
                #      "query GET_DAILY_DEAL_PREVIEWS($portalIds: [Int!]) {\n  dailyDeal {\n    previews(portalIds:"
                #      " $portalIds) {\n      portalId\n      product {\n        ...ProductWithOffer\n       "
                #      " __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment"
                #      " ProductWithOffer on ProductWithOffer {\n  mandatorSpecificData {\n   "
                #      " ...ProductMandatorSpecific\n    __typename\n  }\n  product {\n   "
                #      " ...ProductMandatorIndependent\n    __typename\n  }\n  offer {\n    ...ProductOffer\n   "
                #      " __typename\n  }\n  isDefaultOffer\n  __typename\n}\n\nfragment ProductMandatorSpecific on"
                #      " MandatorSpecificData {\n  isBestseller\n  isDeleted\n  showroomSites\n  sectorIds\n "
                #      " hasVariants\n  __typename\n}\n\nfragment ProductMandatorIndependent on ProductV2 {\n  id\n "
                #      " productId\n  name\n  nameProperties\n  productTypeId\n  productTypeName\n  brandId\n "
                #      " brandName\n  averageRating\n  totalRatings\n  totalQuestions\n  isProductSet\n  images {\n   "
                #      " url\n    height\n    width\n    __typename\n  }\n  energyEfficiency {\n   "
                #      " energyEfficiencyColorType\n    energyEfficiencyLabelText\n    energyEfficiencyLabelSigns\n   "
                #      " energyEfficiencyImage {\n      url\n      height\n      width\n      __typename\n    }\n   "
                #      " __typename\n  }\n  seo {\n    seoProductTypeName\n    seoNameProperties\n    productGroups"
                #      " {\n      productGroup1\n      productGroup2\n      productGroup3\n      productGroup4\n     "
                #      " __typename\n    }\n    gtin\n    __typename\n  }\n  smallDimensions\n  basePrice {\n   "
                #      " priceFactor\n    value\n    __typename\n  }\n  productDataSheet {\n    name\n    languages\n "
                #      "   url\n    size\n    __typename\n  }\n  __typename\n}\n\nfragment ProductOffer on OfferV2 {\n"
                #      "  id\n  productId\n  offerId\n  shopOfferId\n  price {\n    amountIncl\n    amountExcl\n   "
                #      " currency\n    __typename\n  }\n  deliveryOptions {\n    mail {\n      classification\n     "
                #      " futureReleaseDate\n      __typename\n    }\n    pickup {\n      siteId\n     "
                #      " classification\n      futureReleaseDate\n      __typename\n    }\n    detailsProvider {\n    "
                #      "  productId\n      offerId\n      quantity\n      type\n      __typename\n    }\n   "
                #      " __typename\n  }\n  label\n  labelType\n  type\n  volumeDiscountPrices {\n    minAmount\n   "
                #      " price {\n      amountIncl\n      amountExcl\n      currency\n      __typename\n    }\n   "
                #      " isDefault\n    __typename\n  }\n  salesInformation {\n    numberOfItems\n   "
                #      " numberOfItemsSold\n    isEndingSoon\n    validFrom\n    __typename\n  }\n  incentiveText\n "
                #      " isIncentiveCashback\n  isNew\n  isSalesPromotion\n  hideInProductDiscovery\n "
                #      " canAddToBasket\n  hidePrice\n  insteadOfPrice {\n    type\n    price {\n      amountIncl\n   "
                #      "   amountExcl\n      currency\n      __typename\n    }\n    __typename\n  }\n "
                #      " minOrderQuantity\n  __typename\n}\n"
                #  ),
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
            "portal": portal,
            "currency": "CHF",
        }

        info["percent-available"] = (1 - info["quantity-sold"] / info["quantity-total"]) * 100

        yield info


async def brack(session):
    async with session.get("https://daydeal.ch") as response:
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
        "image": html.find(class_="product-tabs__img").href,
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


async def main():
    async with ClientSession() as session:
        tasks = [
            digitec(session),
            brack(session),
        ]

        for result in as_completed(tasks):
            result = await result
            async for offer in result:
                pp(offer)


run(main())
