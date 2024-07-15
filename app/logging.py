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


def update_log_record_factory():
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.event = ""
        return record

    logging.setLogRecordFactory(record_factory)


update_log_record_factory()

telethon_logger = logging.getLogger('telethon')
telethon_logger.setLevel(logging.INFO)


def get_logger(*args, **kwargs):
    return logging.getLogger(*args, **kwargs)
