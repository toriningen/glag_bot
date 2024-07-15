import logging
from pathlib import Path
from typing import List, Iterator

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


def ellipsis_truncate(text: str, max_len: int) -> str:
    if len(text) > max_len:
        return f'{text[:max_len - 3]}...'

    return text


def split_long_text(text: str, max_len: int = 4096) -> Iterator[str]:
    """Attempt to split text by line breaks, so that every chunk is not more than max_len.

    If the split cannot be done by line breaks, then split by whitespace.

    If cannot be done either, split by codepoints."""

    while text:
        closest_lf = text.rfind('\n', 0, max_len)
        if closest_lf != -1:
            yield text[:closest_lf]
            text = text[closest_lf:]
            continue

        closest_whitespace = text.rfind(' ', 0, max_len)
        if closest_whitespace != -1:
            yield text[:closest_whitespace]
            text = text[closest_whitespace:]
            continue

        yield text[:max_len]
        text = text[max_len:]


def make_bot(session: str, tables: List[str]) -> TelegramClient:
    to_glag = build_converter(tables)
    bot = TelegramClient(session, api_id=API_ID, api_hash=API_HASH)

    @bot.on(events.NewMessage(incoming=True, pattern=r'^/start'))
    async def on_start(event):
        await event.reply('Добродошли!')
        raise events.StopPropagation()

    @bot.on(events.NewMessage(incoming=True))
    async def on_new_message(event):
        orig_text = event.raw_text
        glag_text = to_glag(orig_text)

        for chunk in split_long_text(glag_text):
            await event.reply(chunk)

    @bot.on(events.InlineQuery())
    async def inline_handler(event):
        orig_text = event.text
        glag_text = to_glag(orig_text)

        if not glag_text:
            return await event.answer([])

        hint = ''
        if len(orig_text) == 255:
            hint = '(⚠️ можливо, текст занадто довгий - обмеження в 270 знаків) '

        return await event.answer([
            event.builder.article(
                title=f'({len(orig_text)} | {len(glag_text)}) {ellipsis_truncate(glag_text, 100)}',
                description=f"{hint}відправити транслітерацію в чат",
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
