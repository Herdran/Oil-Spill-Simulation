from logging import getLogger
from typing import Set, List, Tuple
from os import PathLike, path
from itertools import product
from zipfile import ZipFile

import numpy as np
import numpy.typing as npt

from simulation.point import Coord_t
from data.measurment_data import Coordinates, CoordinatesBase
from data.utilities import project_coordinates, project_coordinates_reverse
from initial_values import InitialValues
from files import get_binary_world_map_path, get_binary_world_map_zip_path, get_unzipped_world_map_dir_path, \
    get_binary_world_scaled_map_path

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


def _get_binary_map() -> BinaryMap:
    binary_map_path = get_binary_world_map_path()
    if not path.exists(binary_map_path):
        _unzip_world_map()
    return _load_binary_from_file(binary_map_path)


def get_binary_scaled_map() -> BinaryMap:
    binary_map_path = get_binary_world_scaled_map_path()
    if not path.exists(binary_map_path):
        _unzip_world_map()
    return _load_binary_from_file(binary_map_path)


def _get_top_left_offset() -> CoordinatesBase[int]:
    top_left = Coordinates(
        latitude  = InitialValues.simulation_initial_parameters.area.max.latitude,
        longitude = InitialValues.simulation_initial_parameters.area.min.longitude
    )        
    return project_coordinates(top_left, InitialValues.BINARY_MAP_WIDTH, InitialValues.BINARY_MAP_HEIGHT)


def _is_land(binary_map: BinaryMap, top_left_offset: CoordinatesBase[int], x: int, y: int) -> bool:
    bin_x = top_left_offset.longitude + x
    bin_y = top_left_offset.latitude + y   
    index = (bin_y * InitialValues.BINARY_MAP_WIDTH) + bin_x
    return binary_map[index] == 0


def _get_cartesian_product_range() -> product:
    return product(range(InitialValues.point_side_count), range(InitialValues.point_side_count))


def _get_lands_set(binary_map: BinaryMap, top_left_offset: CoordinatesBase[int]) -> Set[Coord_t]:
    logger.debug("STATED: Loading lands set")
    lands = set()
    for x, y in _get_cartesian_product_range():
        if _is_land(binary_map, top_left_offset, x, y):
            lands.add((x, y))
    logger.debug("FINISHED: Loading lands set")
    return lands


def load_topography() -> Set[Coord_t]:        
    return _get_lands_set(_get_binary_map(), _get_top_left_offset())


def project_coordinates_oil_sources_to_simulation(coord: List[float]):
    coord = Coordinates(
        latitude=coord[0],
        longitude=coord[1]
    )
    coordinates = project_coordinates(coord, InitialValues.BINARY_MAP_WIDTH, InitialValues.BINARY_MAP_HEIGHT)

    lon = coordinates.longitude
    lat = coordinates.latitude

    top_left_offset = _get_top_left_offset()

    lon_top_left, lat_top_left = top_left_offset.longitude, top_left_offset.latitude

    return int(lat) - int(lat_top_left), int(lon) - int(lon_top_left)
    # TODO finish after merging with points_count


def project_coordinates_oil_sources_from_simulation(coord: Tuple[int, int]):
    lat, lon = coord[0], coord[1]

    top_left_offset = _get_top_left_offset()

    lon_top_left, lat_top_left = top_left_offset.longitude, top_left_offset.latitude

    lat += lat_top_left
    lon += lon_top_left

    coordinates = project_coordinates_reverse((lat, lon), InitialValues.BINARY_MAP_WIDTH, InitialValues.BINARY_MAP_HEIGHT)

    return round(coordinates[0], 4), round(coordinates[1], 4)
