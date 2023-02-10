from argparse import ArgumentParser
from asyncio import create_task, gather, run
import json
from pathlib import Path

from aiohttp import ClientSession

from daydeal.models import Config, Offer, OfferParser
from daydeal.telegram import update_channel


async def scrape(offer: OfferParser, session: ClientSession) -> Offer:
    print(f"{offer.offer_id}: Scraping website")
    async with session.get(offer.scrape_url) as response:
        print(f"{offer.offer_id}: Extracting website data")
        return offer.evaluate(await response.text())


async def send_off_to_telegram(config: Config, offer: Offer, session: ClientSession):
    print(f"{offer.offer_id}: Posting on telegram")
    log = await update_channel(session, config, offer)
    print(f"{offer.offer_id}: {log}")


async def worker(config: Config, raw_offer: dict, session: ClientSession):
    offer = await scrape(OfferParser.parse_obj(raw_offer), session)
    await send_off_to_telegram(config, offer, session)


async def main(config: Config, raw_offers: dict):
    async with ClientSession() as session:
        await gather(*[create_task(worker(config, offer, session)) for offer in raw_offers])


parser = ArgumentParser("daydeal")
parser.add_argument("-c", "--config", type=Path, help="Config file path")
parser.add_argument("-o", "--offers", type=Path, help="Offers file")
args = parser.parse_args()

config = Config.parse_file(args.config)
offers = json.loads(args.offers.read_text())

run(main(config, offers))
