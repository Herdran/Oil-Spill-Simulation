from itertools import product
from logging import getLogger
from typing import Any

from initial_values import InitialValues
from simulation.point import Coord_t
from topology.math import get_xy_from_coord_raw
from topology.binary_map_math import project_binary_map_xy_to_coordinates_raw
from topology.file_loader import BinaryMap, get_binary_map

import numpy as np


logger = getLogger("topology")


def _is_land(binary_map: BinaryMap, x: int, y: int) -> bool:
    top_left_offset = InitialValues.top_left_binary_offset
    bin_x = top_left_offset.longitude + x
    bin_y = top_left_offset.latitude + y
    bin_x = bin_x - 1 if top_left_offset.longitude > 1 else bin_x
    bin_y = bin_y - 1 if top_left_offset.latitude > 1 else bin_y
    index = (bin_y * InitialValues.BINARY_MAP_WIDTH) + bin_x
    return binary_map[index] == 0


def _get_cartesian_product_range(size_x: int, size_y: int) -> product:
    return product(range(size_x), range(size_y))


def _get_map_range() -> product:
    top_left_offset = InitialValues.top_left_binary_offset
    bottom_right_offset = InitialValues.bottom_right_binary_offset
    size_x = bottom_right_offset.longitude - top_left_offset.longitude
    size_y = bottom_right_offset.latitude - top_left_offset.latitude
    size_x = size_x + 1 if bottom_right_offset.longitude + size_x + 1 < InitialValues.BINARY_MAP_WIDTH else size_x
    size_y = size_y + 1 if bottom_right_offset.latitude + size_y + 1 < InitialValues.BINARY_MAP_HEIGHT else size_y
    size_x = size_x + 1 if bottom_right_offset.longitude > 1 else size_x
    size_y = size_y + 1 if bottom_right_offset.latitude > 1 else size_y
    return _get_cartesian_product_range(size_x, size_y)


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

    top_left_offset = InitialValues.top_left_binary_offset

    xy_points = dict()
    def get_point_xy(lon: float, lat: float) -> (int, int):
        if (lon, lat) not in xy_points:
            xy_points[(lon, lat)] = get_xy_from_coord_raw(lon, lat)
        return xy_points[(lon, lat)]

    projected_to_coords = dict()
    def get_projected_to_coords(x: int, y: int) -> (float, float):
        if (x, y) not in projected_to_coords:
            projected_to_coords[(x, y)] = project_binary_map_xy_to_coordinates_raw(x, y)
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
