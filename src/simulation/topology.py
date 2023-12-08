from logging import getLogger
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


BinaryMap = npt.ArrayLike


BINARY_MAP_WIDTH = 86400
BINARY_MAP_HEIGHT = 43200


logger = getLogger("topology")


def load_binary_from_file(path_to_world_map: PathLike) -> BinaryMap:
    map_bytes = np.fromfile(path_to_world_map, dtype='uint8')
    return np.unpackbits(map_bytes)


def unzip_world_map():
    logger.info("Unzipping world map")
    output_dir = get_unzipped_world_map_dir_path()
    
    with ZipFile(get_binary_world_map_zip_path(), 'r') as zip_ref:
        output_dir.mkdir(parents=True, exist_ok=True)
        zip_ref.extractall(output_dir)
        
    if not path.exists(get_binary_world_map_path()):
        raise FileNotFoundError("World map not found after unzipping")
    
    logger.info("World map has been unzipped successfully and saved to %s", output_dir)

def get_binary_map_path() -> BinaryMap:
    binary_map_path = get_binary_world_map_path()
    if not path.exists(binary_map_path):
        unzip_world_map()    
    return load_binary_from_file(binary_map_path)

def project_binary_map_coordinates(coord: Coordinates) -> CoordinatesBase[int]:
    return project_coordinates(coord, BINARY_MAP_WIDTH, BINARY_MAP_HEIGHT)

def get_top_left_offset() -> CoordinatesBase[int]:
    top_left = Coordinates(
        latitude  = const.point_lat_centers[0],
        longitude = const.point_lon_centers[0]
    )     
    return project_binary_map_coordinates(top_left)

def get_bottom_right_offset() -> CoordinatesBase[int]:
    bottom_right = Coordinates(
        latitude  = const.point_lat_centers[-1],
        longitude = const.point_lon_centers[-1]
    )
    return project_binary_map_coordinates(bottom_right)


def is_land(binary_map: BinaryMap, top_left_offset: CoordinatesBase[int], x: int, y: int) -> bool:
    # TODO: use size from constants! one point here != one bit
    bin_x = top_left_offset.longitude + x
    bin_y = top_left_offset.latitude + y   
    index = (bin_y * BINARY_MAP_WIDTH) + bin_x
    return binary_map[index] == 0


def get_cartesian_product_range(size_x: int, size_y: int) -> product:
     return product(range(size_x), range(size_y))

def get_map_range(top_left_offset: CoordinatesBase[int], bottom_right_offset: CoordinatesBase[int]) -> product:
    size_x = bottom_right_offset.longitude - top_left_offset.longitude
    size_y = bottom_right_offset.latitude - top_left_offset.latitude
    return get_cartesian_product_range(size_x, size_y)


def get_lands_set(binary_map: BinaryMap, top_left_offset: CoordinatesBase[int], bottom_right_offset: CoordinatesBase[int]) -> set[Coord_t]:
    logger.debug("STATED: Loading lands set")
    lands = set()
    for x, y in get_map_range(top_left_offset, bottom_right_offset):
        if is_land(binary_map, top_left_offset, x, y):
            lands.add((x, y))
    logger.debug("FINISHED: Loading lands set")
    return lands

def map_binary_lands(binary_lands: set[Coord_t]) -> set[Coord_t]:
    logger.debug("STATED: Mapping binary lands")
    top_left_binary_map_offset = get_top_left_offset()
    
    def is_land(coord: Coord_t) -> bool:
        center = Coordinates(
            latitude=const.point_lat_centers[coord[1]],
            longitude=const.point_lon_centers[coord[0]]
        )
        binary_map_coordinates = project_binary_map_coordinates(center)
        lat = binary_map_coordinates.longitude - top_left_binary_map_offset.longitude
        lon = binary_map_coordinates.latitude - top_left_binary_map_offset.latitude
        return (lat, lon) in binary_lands
       
    product = get_cartesian_product_range(const.point_side_lon_count, const.point_side_lat_count)
    result = {coord for coord in product if is_land(coord)}
    logger.debug("FINISHED: Mapping binary lands")
    return result


def load_topography() -> set[Coord_t]:        
    binary_lands = get_lands_set(get_binary_map_path(), get_top_left_offset(), get_bottom_right_offset())
    return map_binary_lands(binary_lands)