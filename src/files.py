import os
from pathlib import Path


def get_main_path() -> Path:
    return Path("../") if os.getcwd().endswith('src') else Path("./")

def get_processed_data_path() -> Path:
    return get_main_path().joinpath("data/processed_data")


def get_log_config_path() -> Path:
    return get_main_path().joinpath("src/log_config.conf")


def get_log_output_path() -> Path:
    return get_main_path().joinpath("logs")


def get_world_map_dir_path() -> Path:
    return get_main_path().joinpath("data/world_map")


def get_unzipped_world_map_dir_path() -> Path:
    return get_world_map_dir_path().joinpath("unzipped")


def get_binary_world_map_path() -> Path:
    return get_unzipped_world_map_dir_path().joinpath("full_world_map.bin")


def get_binary_world_scaled_map_path(scale: int):
    return get_unzipped_world_map_dir_path().joinpath(f"{scale}x_scaled_world_map.bin")


def get_binary_world_map_zip_path():
    return get_world_map_dir_path().joinpath("full_world_map.zip")


def get_checkpoint_dir_path():
    return get_main_path().joinpath("checkpoints")
