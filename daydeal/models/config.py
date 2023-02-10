from pathlib import Path

from pydantic import BaseModel


class Config(BaseModel):
    # Chat ID to where we send our Telegram bots
    chat_id: int
    # Telegram bot token acquired via BotFather
    bot_token: str
    # Directory to save offer / message data
    save_dir: Path
