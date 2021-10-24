import logging
import sys

from utils.KoalaUtils import format_config_path, CONFIG_DIR


logging.basicConfig(filename=format_config_path(CONFIG_DIR, 'TwitchAlert.log'),
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s')


logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
