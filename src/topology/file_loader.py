from logging import getLogger
from os import PathLike, path
from zipfile import ZipFile

import numpy.typing as npt
import numpy as np

from files import get_binary_world_map_path, get_binary_world_map_zip_path, get_binary_world_scaled_map_path, get_unzipped_world_map_dir_path


BinaryMap = npt.ArrayLike


logger = getLogger("topology")


def _load_binary_from_file(path_to_world_map: PathLike) -> BinaryMap:
    map_bytes = np.fromfile(path_to_world_map, dtype='uint8')
    return np.unpackbits(map_bytes)


def _unzip_world_map():
    logger.info("Unzipping world map")
    output_dir = get_unzipped_world_map_dir_path()
    
    with ZipFile(get_binary_world_map_zip_path(), 'r') as zip_ref:
        output_dir.mkdir(parents=True, exist_ok=True)
        zip_ref.extractall(output_dir)
        
    if not path.exists(get_binary_world_map_path()):
        raise FileNotFoundError("World map not found after unzipping")
    
    logger.info("World map has been unzipped successfully and saved to %s", output_dir)


def _get_unzipped_world_map(path: PathLike) -> BinaryMap:
    if not path.exists():
        _unzip_world_map()
    return _load_binary_from_file(path)


def get_binary_map() -> BinaryMap:
    return _get_unzipped_world_map(get_binary_world_map_path())


def get_binary_scaled_map() -> BinaryMap:
    return _get_unzipped_world_map(get_binary_world_scaled_map_path())