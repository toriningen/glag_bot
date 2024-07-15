from pathlib import Path
from typing import List

from telethon import TelegramClient, events, Button

from .config import *
from .converter import Converter
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
    converter = Converter({'cyr': UKR_TABLE, 'isv': ISV_TABLE})
    from_cyr = lambda text: converter.convert('cyr', text)
    from_isv = lambda text: converter.convert('isv', text)

    bot = TelegramClient(session, api_id=API_ID, api_hash=API_HASH, catch_up=True)

    async def reply_long(event, text):
        for chunk in split_long_text(text):
            chunk = chunk.strip()
            if chunk:
                await event.reply(chunk)

    @bot.on(events.NewMessage(incoming=True, pattern=r'^/start'))
    async def on_start(event):
        logger.debug(f'Start message', extra=log_event(event))

        await event.reply(f'{from_cyr('Вітаю!')} {from_isv('Добродошли!')}')
        raise events.StopPropagation()

    @bot.on(events.NewMessage(incoming=True))
    async def on_new_message(event):
        logger.debug(f'New message', extra=log_event(event))

        orig_text = event.raw_text
        langs = converter.detect(orig_text)
        if len(langs) == 1:
            lang, = langs
            glag_text = converter.convert(lang, orig_text)
            return await reply_long(event, glag_text)
        else:
            candidates = set([converter.convert(lang, orig_text) for lang in langs])
            if len(candidates) == 1:
                glag_text = candidates.pop()
                return await reply_long(event, glag_text)
            else:
                await event.reply("⚠️ Яка це мова?", buttons=[
                    [Button.inline("українська", 'ukr'), Button.inline("міжслов'янська", 'isv')]
                ])

    @bot.on(events.CallbackQuery())
    async def on_button(event):
        data = event.data.decode('utf-8')
        if data == 'ukr':
            await event.answer('ukr clicked!')
        elif data == 'isv':
            await event.answer('isv clicked!')

    @bot.on(events.InlineQuery())
    async def inline_handler(event):
        logger.debug(f'Inline query', extra=log_event(event.original_update))

        orig_text = event.text
        if not orig_text:
            return await event.answer([])

        langs = converter.detect(orig_text)
        options = []
        if len(orig_text) >= 255:
            options.append(event.builder.article(
                title='⚠️ можливо, текст занадто довгий!',
                description='Якщо вам потрібно перетворити довший текст, напишіть боту в особисті.',
                text='',
            ))

        lang_names = {
            'ukr': "українська",
            'isv': "меджусловјанскы",
        }

        for lang, lang_name in langs.items():
            glag_text = converter.convert(lang, orig_text)
            options.append(event.builder.article(
                title=ellipsis_truncate(glag_text, 100),
                description=lang_names[lang],
                text=glag_text,
            ))

        return await event.answer(options, cache_time=CACHE_TIME)

    return bot


async def main():
    logger.info("Starting bot...")

    var_run = Path('/var/run')
    if not var_run.exists():
        var_run = Path('.')

    session_root = var_run / 'sessions'
    session_root.mkdir(exist_ok=True)

    bot = make_bot(str(session_root / 'to_glag_bot'), [UKR_TABLE, ISV_TABLE])
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()
