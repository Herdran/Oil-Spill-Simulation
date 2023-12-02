from typing import Set
from os import PathLike, path
from itertools import product
from zipfile import ZipFile

import numpy as np
import numpy.typing as npt

from simulation.point import Coord_t
from data.measurment_data import Coordinates, CoordinatesBase
from data.utilities import project_coordinates
from constatnts import Constants as const
from files import get_binary_world_map_path, get_binary_world_map_zip_path, get_unzipped_world_map_dir_path


BINARY_MAP_WIDTH = 86400
BINARY_MAP_HEIGHT = 43200


BinaryMap = npt.ArrayLike


def load_binary_from_file(path_to_world_map: PathLike) -> BinaryMap:
    map_bytes = np.fromfile(path_to_world_map, dtype='uint8')
    return np.unpackbits(map_bytes)


def unzip_world_map():
    output_dir = get_unzipped_world_map_dir_path()
    with ZipFile(get_binary_world_map_zip_path(), 'r') as zip_ref:
        output_dir.mkdir(parents=True, exist_ok=True)
        zip_ref.extractall(output_dir)


def get_binary_map_path() -> BinaryMap:
    binary_map_path = get_binary_world_map_path()
    if not path.exists(binary_map_path):
        unzip_world_map()    
    return load_binary_from_file(binary_map_path)


def get_top_left_offset() -> CoordinatesBase[int]:
    top_left = Coordinates(
        latitude  = const.SIMULATION_INITIAL_PARAMETERS.area.max.latitude,
        longitude = const.SIMULATION_INITIAL_PARAMETERS.area.min.longitude
    )        
    return project_coordinates(top_left, BINARY_MAP_WIDTH, BINARY_MAP_HEIGHT)


def is_land(binary_map: BinaryMap, top_left_offset: CoordinatesBase[int], x: int, y: int) -> bool:
    bin_x = top_left_offset.longitude + x
    bin_y = top_left_offset.latitude + y   
    index = (bin_y * BINARY_MAP_WIDTH) + bin_x
    return binary_map[index] == 0


def get_cartesian_product_range() -> product:
    return product(range(const.POINTS_SIDE_COUNT), range(const.POINTS_SIDE_COUNT))


def get_lands_set(binary_map: BinaryMap, top_left_offset: CoordinatesBase[int]) -> Set[Coord_t]:
    lands = set()
    for x, y in get_cartesian_product_range():
        if is_land(binary_map, top_left_offset, x, y):
            lands.add((x, y))
    return lands


def load_topography() -> Set[Coord_t]:        
    return get_lands_set(get_binary_map_path(), get_top_left_offset())