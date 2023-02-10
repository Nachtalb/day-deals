import json

from aiohttp import ClientSession

from daydeal.models import Config, Message, Offer
from daydeal.text import get_full_post


def get_markup(offer: Offer, is_over: bool = False) -> str:
    return json.dumps(
        {
            "inline_keyboard": [
                [
                    {
                        "text": "Angebot Vorbei" if is_over else "Jetzt Profitieren ➡️",
                        "url": offer.url,  # type: ignore
                    }
                ]
            ]
        }
    )


async def api_post(session: ClientSession, config: Config, endpoint: str, data: dict) -> tuple[bool, dict, str]:
    data["chat_id"] = config.chat_id
    async with session.get(f"https://api.telegram.org/bot{config.bot_token}/{endpoint}", data=data) as response:
        response_data = await response.json()
        return response_data["ok"], response_data.get("result"), response_data.get("description", "")


async def post_to_telegram(
    session: ClientSession, config: Config, offer: Offer, previous_message: Message | None
) -> tuple[str, Message | None]:
    old_message = {}

    if previous_message and previous_message.offer == offer:
        return "Nothing changed", previous_message

    method = "sendMessage"
    new_message: dict[str, str | int] = {
        "text": get_full_post(offer),
        "reply_markup": get_markup(offer),
        "parse_mode": "html",
    }
    is_new = True

    if previous_message and previous_message != offer and previous_message.offer.sale_id == offer.sale_id:
        method = "editMessageText"
        new_message["message_id"] = previous_message.message_id
        is_new = False

    ok, message_data, error = await api_post(session, config, method, new_message)

    if not ok:
        return "🔴 Could not send new/updated message: " + error, previous_message

    message = Message(
        chat_type=message_data["chat"]["type"],
        chat_id=message_data["chat"]["id"],
        chat_username=message_data["chat"].get("username"),
        message_id=message_data["message_id"],
        offer=offer,
    )

    if previous_message and previous_message.offer.sale_id != offer.sale_id:
        old_message = {
            "text": get_full_post(offer, message.link),
            "reply_markup": get_markup(offer, True),
            "message_id": previous_message.message_id,
            "parse_mode": "html",
        }
        ok, message_data, error = await api_post(session, config, "editMessageText", old_message)
        if not ok:
            return f"🔴 Could not send new/updated message: " + error, message

    return "🟢 Message posted" if is_new else "🔵 Message changed", message


async def update_channel(session: ClientSession, config: Config, offer: Offer) -> str:
    message_file = config.save_dir / f"{offer.offer_id}.json"
    previous_message = Message.parse_file(message_file) if message_file.is_file() else None
    log, message = await post_to_telegram(session, config, offer, previous_message)
    if message:
        message_file.write_text(message.json())
    return log
