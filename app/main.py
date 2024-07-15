import logging

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

def make_bot(token: str, table: str) -> TelegramClient:
    to_glag = build_converter(table)
    bot = TelegramClient('bot', api_id=API_ID, api_hash=API_HASH).start(bot_token=token)

    @bot.on(events.NewMessage())
    async def on_new_message(event):
        await event.reply(to_glag(event.message))

    return bot


async def main():
    logger.info("Starting bot...")

    # cyr_bot = make_bot(CYR_BOT_TOKEN, CYR_TABLE)
    # isv_bot = make_bot(ISV_BOT_TOKEN, ISV_TABLE)
    bot = make_bot(BOT_TOKEN, '\n'.join([CYR_TABLE, ISV_TABLE]))
    bot.run_until_disconnected()
