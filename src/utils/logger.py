import logging

import colorlog

from src.config import settings

_FORMAT = "%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(cyan)s%(name)s%(reset)s: %(message)s"


def get_logger(name: str, level: int | str | None = None) -> logging.Logger:
    """Return a logger that prints colored records to stderr (configured once per name).

    The level defaults to LOG_LEVEL from the settings.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(_FORMAT, datefmt="%H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(level or settings.log_level.upper())
        logger.propagate = False
    return logger
