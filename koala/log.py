import sys
import logging
from datetime import date

from pathlib import Path

from koala.utils import format_config_path
from koala.env import CONFIG_PATH, LOGGING_FILE

# load_dotenv()
_LOG_LEVEL = logging.DEBUG
_FORMATTER = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
_LOG_DIR = format_config_path(CONFIG_PATH, "logs", str(date.today()))

Path(_LOG_DIR).mkdir(exist_ok=True, parents=True)


# logging.basicConfig(filename=format_config_path(_LOG_DIR, 'KoalaBot.log'),
#                     level=logging.WARN,
#                     format='%(asctime)s %(levelname)-8s %(message)s')


def _get_default_warn_log():
    koala_log = logging.FileHandler(filename=format_config_path(_LOG_DIR, "KoalaBotWarn.log"))
    koala_log.setFormatter(_FORMATTER)
    koala_log.setLevel(logging.WARN)
    return koala_log


def _get_file_handler(log_name, log_level):
    file_handler = logging.FileHandler(filename=format_config_path(_LOG_DIR, log_name))
    file_handler.setFormatter(_FORMATTER)
    file_handler.setLevel(log_level)
    return file_handler


def _get_stdout_stream_handler(log_level):
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(_FORMATTER)
    stream_handler.setLevel(log_level)
    return stream_handler


def get_logger(log_name, log_level=_LOG_LEVEL, file_name=None, file_handler=True, stdout_handler=True):
    new_logger = logging.getLogger(log_name)

    if file_handler and LOGGING_FILE:
        new_logger.addHandler(_get_file_handler(file_name if file_name else log_name, log_level))
        new_logger.addHandler(_get_default_warn_log())

    if stdout_handler:
        new_logger.addHandler(_get_stdout_stream_handler(log_level))

    new_logger.setLevel(log_level)

    return new_logger


logger = get_logger(__name__)

discord_logger = get_logger("discord", log_level=logging.WARN, file_name="discord.log", stdout_handler=False)


