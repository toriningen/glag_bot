import json
from pathlib import Path

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


def make_bot(session: str) -> TelegramClient:
    converter = Converter()
    from_ukr = lambda text: converter.convert('ukr', text)
    from_isv = lambda text: converter.convert('isv', text)

    pending_messages = {}  # chat_id -> (text event, lang question event)

    bot = TelegramClient(session, api_id=API_ID, api_hash=API_HASH, catch_up=True)

    async def handle_message_with_known_lang(lang, event):
        orig_text = event.raw_text
        glag_text = converter.convert(lang, orig_text)
        await handle_message_with_known_text(event, glag_text)

    async def handle_message_with_known_text(event, glag_text):
        for chunk in split_long_text(glag_text):
            chunk = chunk.strip()
            if chunk:
                await event.reply(chunk)

    @bot.on(events.NewMessage(incoming=True, pattern=r'^/start'))
    async def on_start(event):
        logger.debug(f'Start message', extra=log_event(event))

        await event.reply(f'{from_ukr('Вітаю!')} {from_isv('Добродошли!')}')
        raise events.StopPropagation()

    @bot.on(events.NewMessage(incoming=True))
    async def on_new_message(event):
        logger.debug(f'New message', extra=log_event(event))

        orig_text = event.raw_text
        langs = converter.detect_lang(orig_text)
        if len(langs) == 1:
            lang, = langs
            return await handle_message_with_known_lang(lang, event)

        # TODO: only show languages for unique candidates... but since we have just two languages yet, no point :D
        candidates = {
            from_ukr(orig_text),
            from_isv(orig_text),
        }

        if len(candidates) == 1:
            return await handle_message_with_known_text(event, candidates.pop())

        lang_names = {
            'ukr': "українською",
            'isv': "міжслов'янською",
        }

        # do we already have a pending question for this chat? if so, kill it
        chat_id = event.chat_id
        if chat_id in pending_messages:
            _, lang_event = pending_messages[chat_id]
            await lang_event.delete()
            del pending_messages[chat_id]

        lang_event = await event.reply("⚠️ Якою це мовою?", buttons=[
            [Button.inline(lang_name, lang) for lang, lang_name in lang_names.items()]
        ])
        pending_messages[chat_id] = (event, lang_event)

    @bot.on(events.CallbackQuery())
    async def on_button(event):
        logger.debug(f'New callback query', extra=log_event(event.original_update))
        lang = event.data.decode('utf8')
        chat_id = event.chat_id
        if chat_id in pending_messages:
            await handle_message_with_known_lang(lang, pending_messages[chat_id][0])
            await event.delete()
            del pending_messages[chat_id]

    @bot.on(events.InlineQuery())
    async def inline_handler(event):
        logger.debug(f'Inline query', extra=log_event(event.original_update))

        orig_text = event.text
        if not orig_text:
            return await event.answer([])

        options = []
        if len(orig_text) >= 255:
            options.append(event.builder.article(
                title='⚠️ Текст занадто довгий!',
                description='Напишіть боту в особисті, якщо вам потрібно перетворити довший текст.',
                text=r'¯\_(ツ)_/¯',
            ))

        lang_names = {
            'ukr': "українська",
            'isv': "меджусловјанскы",
        }

        def add_lang_option(lang):
            glag_text = converter.convert(lang, orig_text)
            options.append(event.builder.article(
                title=ellipsis_truncate(glag_text, 100),
                description=lang_names[lang],
                text=glag_text,
            ))

        def add_text_option(glag_text):
            options.append(event.builder.article(
                title=ellipsis_truncate(glag_text, 100),
                description='надіслати в чат',
                text=glag_text,
            ))

        def add_dbg(arg):
            options.append(event.builder.article(
                title=f'dbg: {arg}',
                description='dbg',
                text='dbg',
            ))


        def add_candidates():
            candidates = {lang: converter.convert(lang, orig_text) for lang in lang_names}
            candidate_texts = set(candidates.values())
            # add_dbg(f'candidates {candidate_texts!r}')

            if len(candidate_texts) == 1:
                add_text_option(candidate_texts.pop())
            else:
                for lang in lang_names:
                    add_lang_option(lang)

        langs = converter.detect_lang(orig_text)
        # add_dbg(f'detected langs {langs!r}')
        if langs:
            if len(langs) == 1:
                for lang in langs:
                    add_lang_option(lang)
            else:
                add_candidates()
        else:
            add_candidates()

        return await event.answer(options, cache_time=CACHE_TIME)

    return bot


async def main():
    logger.info("Starting bot...")

    var_run = Path('/var/run')
    if not var_run.exists():
        var_run = Path('.')

    session_root = var_run / 'sessions'
    session_root.mkdir(exist_ok=True)

    bot = make_bot(str(session_root / 'to_glag_bot'))
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()
