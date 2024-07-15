import logging
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


def make_bot(tables: List[str]) -> TelegramClient:
    to_glag = build_converter(tables)
    bot = TelegramClient('bot', api_id=API_ID, api_hash=API_HASH)

    @bot.on(events.NewMessage(incoming=True, pattern=r'^/start'))
    async def on_start(event):
        await event.reply('Добродошли!')

    @bot.on(events.NewMessage(incoming=True))
    async def on_new_message(event):
        await event.reply(to_glag(event.raw_text))

    @bot.on(events.InlineQuery())
    async def inline_handler(event):
        await event.answer([
            event.builder.article(
                title=f"title: {to_glag(event.text)}",
                description="desc",
                text=to_glag(event.text)
            )
        ])

    return bot

async def main():
    logger.info("Starting bot...")

    bot = make_bot([CYR_TABLE, ISV_TABLE])
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()
