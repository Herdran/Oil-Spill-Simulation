from logging import config
from time import strftime

from files import get_log_config_path, get_log_output_path

def init_logger():
    date_str = strftime("%Y-%m-%d_%H-%M-%S")
    logger_output_path = get_log_output_path().joinpath(f"log_{date_str}.logs")
    config.fileConfig(get_log_config_path(), defaults={'logfilename': str(logger_output_path)})
