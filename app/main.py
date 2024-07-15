import logging
from pathlib import Path
from typing import List

from telethon import TelegramClient, events

from .config import *
from .converter import build_converter
from .tables import *

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def round_up(text: str, max_len: int) -> str:
    if len(text) > max_len:
        return f'{text[:max_len - 3]}...'

    return text


def make_bot(session: str, tables: List[str]) -> TelegramClient:
    to_glag = build_converter(tables)
    bot = TelegramClient(session, api_id=API_ID, api_hash=API_HASH)

    @bot.on(events.NewMessage(incoming=True, pattern=r'^/start'))
    async def on_start(event):
        await event.reply('Добродошли!')
        raise events.StopPropagation()

    @bot.on(events.NewMessage(incoming=True))
    async def on_new_message(event):
        await event.reply(to_glag(event.raw_text))

    @bot.on(events.InlineQuery())
    async def inline_handler(event):
        glag_text = to_glag(event.text)

        if not glag_text:
            await event.answer([])
            return

        await event.answer([
            event.builder.article(
                title=round_up(glag_text, 10000),
                description="на глаголицю",
                text=glag_text,
            )
        ])

    return bot


async def main():
    logger.info("Starting bot...")

    session_root = Path('/var/run/sessions/')
    session_root.mkdir(exist_ok=True)

    bot = make_bot(str(session_root / 'to_glag_bot'), [CYR_TABLE, ISV_TABLE])
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()
