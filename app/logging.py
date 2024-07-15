import logging

from app.config import LOG_LEVEL

logging.basicConfig(
    level=logging.getLevelName(LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s | %(event)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler()
    ],
)

telethon_logger = logging.getLogger('telethon')
telethon_logger.setLevel(logging.INFO)


def get_logger(*args, **kwargs):
    return logging.LoggerAdapter(logging.getLogger(*args, **kwargs), {'event': ''})
