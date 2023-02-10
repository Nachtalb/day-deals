from datetime import datetime

from daydeal.models import Offer


def get_availability(offer: Offer) -> str:
    if offer.available_percentage is None:
        return "🟢 Angebot läuft noch!"
    elif offer.available_percentage == 0:
        message = "🔴 Ausverkauft! Nächstes Angebot startet in " + get_next_sale(offer)
    else:
        threshold = {50: "🟢", 25: "🔵", 10: "🟡", 1: "🟠"}
        for threshold, indicator in threshold.items():
            if offer.available_percentage >= threshold:  # type: ignore
                message = indicator
                if offer.available_total:
                    message += f" Noch {offer.available_still}/{offer.available_total} Stück verfügbar!"
                else:
                    message += f" Noch {offer.available_percentage}% verfügbar!"
                break
    return message  # type: ignore


def sale_over(new_message_url: str | None = None):
    over = "🔴 Dieses angebot ist vorbei."
    if new_message_url:
        return f'{over} <a href="{new_message_url}">Zum neuen Angebot!</a>'
    return over


def get_next_sale(offer: Offer) -> str:
    delta = offer.scheduled_next - datetime.now()  # type: ignore
    string = ""

    # days
    match delta.days:
        case x if x == 1:
            string += "einem Tag "
        case x if x > 1:
            string += f"{x} Tagen "

    if string:
        string += "und "

    # minutes
    match delta.seconds // 60 // 60:
        case x if x == 1:
            string += "einer Stunde "
        case x if x > 1:
            string += f"{x} Stunden "
    return string


def get_rating(offer: Offer) -> str:
    if offer.rating is None or offer.rating_top is None:
        return ""
    return round(offer.rating) * "★" + ((offer.rating_top - round(offer.rating)) * "☆")


def get_price(offer: Offer) -> str:
    if offer.price_discount and offer.price_discount != offer.price_full:
        return f"<s>{offer.price_full}</s> {offer.price_discount}"
    return offer.price_full  # type: ignore


def get_image(offer: Offer) -> str:
    return f'<a href="{offer.image}">​</a>'


def get_full_post(offer: Offer, new_message_url: str | None = None) -> str:
    return """<b>🏬 {retailer_name} {sale_id}</b>
{image}
<b>📦 {name} {rating}</b>
{summary}

{availability}

💸 {price}
    """.format(
        retailer_name=offer.retailer_name,
        sale_id=offer.sale_id,
        name=offer.title,
        rating=get_rating(offer),
        summary=offer.summary,
        availability=sale_over(new_message_url) if new_message_url else get_availability(offer),
        price=get_price(offer),
        image=get_image(offer),
    )
