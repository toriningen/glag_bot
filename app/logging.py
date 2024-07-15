import logging

from app.config import LOG_LEVEL

stream_handler = logging.StreamHandler()

formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s | %(event)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    defaults={"event": ""}
)

stream_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.getLevelName(LOG_LEVEL),
    handlers=[stream_handler],
)

telethon_logger = logging.getLogger('telethon')
telethon_logger.setLevel(logging.INFO)

get_logger = logging.getLogger
