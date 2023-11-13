import os
from pathlib import Path

def get_main_path():
    return Path("../") if os.getcwd().endswith('src') else Path("./")

def get_data_path():
    return get_main_path().joinpath("data/processed_data")

def get_log_config_path():
    return get_main_path().joinpath("src/log_config.conf")

def get_log_output_path():
    return get_main_path().joinpath("logs")