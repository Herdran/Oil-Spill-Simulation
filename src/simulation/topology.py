from itertools import product
from logging import getLogger
from math import cos, sin, radians
from os import PathLike, path
from typing import Any
from zipfile import ZipFile

import numpy as np
import numpy.typing as npt
from numpy import ndarray

from data.measurment_data import Coordinates, CoordinatesBase
from data.utilities import calculate_compass_bearing_and_dist, project_coordinates_raw, project_to_coordinates_raw, \
    project_coordinates
from files import get_binary_world_map_path, get_binary_world_map_zip_path, get_unzipped_world_map_dir_path, \
    get_binary_world_scaled_map_path
from initial_values import InitialValues
from simulation.point import Coord_t

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


def project_binary_map_coordinates(coord: Coordinates) -> CoordinatesBase[int]:
    return project_coordinates(coord, InitialValues.BINARY_MAP_WIDTH, InitialValues.BINARY_MAP_HEIGHT)


def project_binary_map_coordinates_raw(lat: float, lon: float) -> (float, float):
    return project_coordinates_raw(lat, lon, InitialValues.BINARY_MAP_WIDTH, InitialValues.BINARY_MAP_HEIGHT)


def get_top_left_offset() -> CoordinatesBase[int]:
    return project_binary_map_coordinates(InitialValues.top_left_coord)


def get_bottom_right_offset() -> CoordinatesBase[int]:
    return project_binary_map_coordinates(InitialValues.bottom_right_coord)


def _is_land(binary_map: BinaryMap, top_left_offset: CoordinatesBase[int], x: int, y: int) -> bool:
    bin_x = top_left_offset.longitude + x
    bin_y = top_left_offset.latitude + y
    bin_x = bin_x - 1 if top_left_offset.longitude > 1 else bin_x
    bin_y = bin_y - 1 if top_left_offset.latitude > 1 else bin_y
    index = (bin_y * InitialValues.BINARY_MAP_WIDTH) + bin_x
    return binary_map[index] == 0


def get_cartesian_product_range(size_x: int, size_y: int) -> product:
    return product(range(size_x), range(size_y))


def get_map_range(top_left_offset: CoordinatesBase[int], bottom_right_offset: CoordinatesBase[int]) -> product:
    size_x = bottom_right_offset.longitude - top_left_offset.longitude
    size_y = bottom_right_offset.latitude - top_left_offset.latitude
    size_x = size_x + 1 if bottom_right_offset.longitude + size_x + 1 < InitialValues.BINARY_MAP_WIDTH else size_x
    size_y = size_y + 1 if bottom_right_offset.latitude + size_y + 1 < InitialValues.BINARY_MAP_HEIGHT else size_y
    size_x = size_x + 1 if bottom_right_offset.longitude > 1 else size_x
    size_y = size_y + 1 if bottom_right_offset.latitude > 1 else size_y
    return get_cartesian_product_range(size_x, size_y)


def get_lands_set(binary_map: BinaryMap, top_left_offset: CoordinatesBase[int], bottom_right_offset: CoordinatesBase[int]) -> set[tuple[Any, Any]]:
    logger.debug("STATED: Loading lands set")
    lands = set()

    for x, y in get_map_range(top_left_offset, bottom_right_offset):
        if _is_land(binary_map, top_left_offset, x, y):
            lands.add((x, y))

    logger.debug("FINISHED: Loading lands set")

    return lands


def map_binary_lands(binary_lands: set[Coord_t]) -> tuple[set[tuple[int, int]], ndarray, ndarray]:
    logger.debug("STATED: Mapping binary lands")
    BEARING_OFFSET = 90.0

    top_left_offset = get_top_left_offset()

    def calculate_point_xy(lon: float, lat: float) -> (int, int):
        bearing, distance = calculate_compass_bearing_and_dist(InitialValues.top_left_coord,
                                                               Coordinates(latitude=lat, longitude=lon))
        rad = radians(bearing - BEARING_OFFSET)
        x = int(distance * cos(rad)) // InitialValues.point_side_size
        y = int(distance * sin(rad)) // InitialValues.point_side_size
        return min(x, InitialValues.point_side_lon_count), min(y, InitialValues.point_side_lat_count)

    xy_points = dict()

    def get_point_xy(lon: float, lat: float) -> (int, int):
        if (lon, lat) not in xy_points:
            xy_points[(lon, lat)] = calculate_point_xy(lon, lat)
        return xy_points[(lon, lat)]

    projected_to_coords = dict()

    def get_projected_to_coords(x: int, y: int) -> (float, float):
        if (x, y) not in projected_to_coords:
            projected_to_coords[(x, y)] = project_to_coordinates_raw(x, y, InitialValues.BINARY_MAP_WIDTH, InitialValues.BINARY_MAP_HEIGHT)
        return projected_to_coords[(x, y)]

    result = set()
    x_indices = []
    y_indices = []

    for x, y in binary_lands:
        x += top_left_offset.longitude
        y += top_left_offset.latitude

        vertex_top_left = get_projected_to_coords(x, y)
        vertex_bottom_right = get_projected_to_coords(x + 1, y + 1)
        vertex_top_right = get_projected_to_coords(x + 1, y)
        vertex_bottom_left = get_projected_to_coords(x, y + 1)

        vertex_top_left_x, vertex_top_left_y = get_point_xy(vertex_top_left[0], vertex_top_left[1])
        vertex_bottom_right_x, vertex_bottom_right_y = get_point_xy(vertex_bottom_right[0], vertex_bottom_right[1])
        vertex_top_right_x, vertex_top_right_y = get_point_xy(vertex_top_right[0], vertex_top_right[1])
        vertex_bottom_left_x, vertex_bottom_left_y = get_point_xy(vertex_bottom_left[0], vertex_bottom_left[1])

        max_y = max(vertex_top_left_y, vertex_bottom_right_y, vertex_top_right_y, vertex_bottom_left_y)
        min_y = min(vertex_top_left_y, vertex_bottom_right_y, vertex_top_right_y, vertex_bottom_left_y)
        max_x = max(vertex_top_left_x, vertex_bottom_right_x, vertex_top_right_x, vertex_bottom_left_x)
        min_x = min(vertex_top_left_x, vertex_bottom_right_x, vertex_top_right_x, vertex_bottom_left_x)

        max_y = min(max_y, InitialValues.point_side_lat_count)
        max_x = min(max_x, InitialValues.point_side_lon_count)

        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                result.add((x, y))
                x_indices.append(x)
                y_indices.append(y)

    x_indices = np.array(x_indices, dtype=int)
    y_indices = np.array(y_indices, dtype=int)

    logger.debug("FINISHED: Mapping binary lands")

    return result, x_indices, y_indices


def load_topography() -> tuple[set[tuple[Any, Any]], ndarray, ndarray]:
    binary_lands = get_lands_set(_get_binary_map(), get_top_left_offset(), get_bottom_right_offset())
    return map_binary_lands(binary_lands)
