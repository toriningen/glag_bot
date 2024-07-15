from pathlib import Path
from typing import List

from telethon import TelegramClient, events

from .config import *
from .converter import build_converter
from .logging import get_logger
from .tables import *
from .text_util import split_long_text

logger = get_logger(__name__)


def ellipsis_truncate(text: str, max_len: int) -> str:
    if len(text) > max_len:
        return f'{text[:max_len - 3]}...'

    return text

def log_event(event):
    return {
        'event': event.to_json(ensure_ascii=False),
    }

def make_bot(session: str, tables: List[str]) -> TelegramClient:
    to_glag = build_converter(tables)
    bot = TelegramClient(session, api_id=API_ID, api_hash=API_HASH)

    @bot.on(events.NewMessage(incoming=True, pattern=r'^/start'))
    async def on_start(event):
        logger.debug(f'Start message', extra=log_event(event))

        await event.reply(to_glag('Добродошли!'))
        raise events.StopPropagation()

    @bot.on(events.NewMessage(incoming=True))
    async def on_new_message(event):
        logger.debug(f'New message', extra=log_event(event))

        orig_text = event.raw_text
        glag_text = to_glag(orig_text)

        for chunk in split_long_text(glag_text):
            chunk = chunk.strip()
            if chunk:
                await event.reply(chunk)

    @bot.on(events.InlineQuery())
    async def inline_handler(event):
        logger.debug(f'Inline query', extra=log_event(event.original_update))

        orig_text = event.text
        glag_text = to_glag(orig_text)

        if not glag_text:
            return await event.answer([])

        hint = 'надіслати транслітерацію в чат'
        if len(orig_text) >= 255:
            hint = '⚠️ можливо, текст занадто довгий!'

        return await event.answer([
            event.builder.article(
                title=f'{ellipsis_truncate(glag_text, 100)}',
                description=f"{hint}",
                text=glag_text,
            )
        ], cache_time=CACHE_TIME)

    return bot


async def main():
    logger.info("Starting bot...")

    session_root = Path('/var/run/sessions/')
    session_root.mkdir(exist_ok=True)

    bot = make_bot(str(session_root / 'to_glag_bot'), [CYR_TABLE, ISV_TABLE])
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()
