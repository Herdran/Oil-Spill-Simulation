from logging import config
from time import strftime

from files import get_log_config_path, get_log_output_path

def get_logger_output_path():
    date_str = strftime("%Y-%m-%d_%H-%M-%S")
    logger_path = get_log_output_path()
    logger_path.mkdir(parents=True, exist_ok=True)
    return logger_path.joinpath(f"log_{date_str}.logs")

def init_logger():
    config.fileConfig(get_log_config_path(), defaults={'logfilename': str(get_logger_output_path())})
