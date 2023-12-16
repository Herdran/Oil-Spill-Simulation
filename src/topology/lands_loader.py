from itertools import product
from logging import getLogger
from typing import Any

from initial_values import InitialValues
from simulation.point import Coord_t
from topology.math import get_xy_from_coord_raw
from topology.binary_map_math import project_binary_map_xy_to_coordinates_raw, project_latitude_to_y, project_longitude_to_x
from topology.file_loader import BinaryMap, get_binary_map

import numpy as np


logger = getLogger("topology")


def _is_land(binary_map: BinaryMap, x: int, y: int) -> bool:
    index = (y * InitialValues.BINARY_MAP_WIDTH) + x
    return binary_map[index] == 0


def _get_map_range() -> product:
    ADDITIONAL_RANGE = 1
    max_x = project_longitude_to_x(InitialValues.max_lon)
    min_x = project_longitude_to_x(InitialValues.min_lon)
    min_y = project_latitude_to_y(InitialValues.max_lat)
    max_y = project_latitude_to_y(InitialValues.min_lat)
    max_x = min(max_x + ADDITIONAL_RANGE, InitialValues.BINARY_MAP_WIDTH)
    max_y = min(max_y + ADDITIONAL_RANGE, InitialValues.BINARY_MAP_HEIGHT)
    min_y = max(min_y - ADDITIONAL_RANGE, 0)
    min_x = max(min_x - ADDITIONAL_RANGE, 0)
    return product(range(min_x, max_x + 1), range(min_y, max_y + 1))


def _get_lands_set(binary_map: BinaryMap) -> set[tuple[Any, Any]]:
    logger.debug("STATED: Loading lands set")
    lands = set()

    for x, y in _get_map_range():
        if _is_land(binary_map, x, y):
            lands.add((x, y))

    logger.debug("FINISHED: Loading lands set")
    return lands


def _map_binary_lands(binary_lands: set[Coord_t]) -> tuple[set[tuple[int, int]], np.ndarray, np.ndarray]:
    logger.debug("STATED: Mapping binary lands")

    xy_points = dict()
    def get_point_xy(lon: float, lat: float) -> tuple[int, int]:
        if (lon, lat) not in xy_points:
            xy_points[(lon, lat)] = get_xy_from_coord_raw(lon, lat)
        return xy_points[(lon, lat)]

    projected_to_coords = dict()
    def get_projected_to_coords(x: int, y: int) -> tuple[float, float]:
        if (x, y) not in projected_to_coords:
            projected_to_coords[(x, y)] = project_binary_map_xy_to_coordinates_raw(x, y)
        return projected_to_coords[(x, y)]

    result = set()
    x_indices = []
    y_indices = []

    for x, y in binary_lands:
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
        min_x = max(min_x, 0)
        min_y = max(min_y, 0)

        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                result.add((x, y))
                x_indices.append(x)
                y_indices.append(y)

    x_indices = np.array(x_indices, dtype=int)
    y_indices = np.array(y_indices, dtype=int)

    logger.debug("FINISHED: Mapping binary lands")

    return result, x_indices, y_indices


def load_topography() -> tuple[set[tuple[Any, Any]], np.ndarray, np.ndarray]:
    binary_lands = _get_lands_set(get_binary_map())
    return _map_binary_lands(binary_lands)
