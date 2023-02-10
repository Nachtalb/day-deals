from pathlib import Path

from pydantic import BaseModel

from daydeal.models.offer import Offer


class Message(BaseModel):
    chat_type: str
    chat_id: int
    chat_username: str | None

    message_id: int

    offer: Offer

    @property
    def link(self) -> str | None:
        if self.chat_type not in ["private", "group"]:
            if self.chat_username:
                to_link = self.chat_username
            else:
                # Get rid of leading -100 for supergroups
                to_link = f"c/{str(self.chat_id)[4:]}"
            return f"https://t.me/{to_link}/{self.message_id}"
        return
