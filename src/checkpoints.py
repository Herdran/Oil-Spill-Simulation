import json
import time
from logging import getLogger
from os import PathLike
from typing import Any

import pandas as pd

from files import get_checkpoint_dir_path
from initial_values import InitialValues
from simulation.point import Point, Coord_t
from topology.math import get_coordinate_from_xy_cached

logger = getLogger("checkpoints")


def _point_to_dict(point: Point) -> dict[str, any]:
    coordinate = get_coordinate_from_xy_cached(point.coord)
    return {
        "coord": point.coord,
        "coordinates": {
            "latitude": coordinate.latitude,
            "longitude": coordinate.longitude
        },
        "oil_mass": point.oil_mass,
        "evaporation_rate": point.evaporation_rate,
        "emulsification_rate": point.emulsification_rate,
        "viscosity_dynamic": point.viscosity_dynamic
    }


def _oil_source_to_dict(source: tuple[Coord_t, int, pd.Timestamp, pd.Timestamp]) -> dict[str, any]:
    lon, lat = get_coordinate_from_xy_cached(source[0]).as_tuple()
    return {
        "coord": (lon, lat),
        "mass_per_minute": source[1],
        "spill_start": str(source[2]),
        "spill_end": str(source[3])
    }


def _get_name_to_save(curr_iter: int) -> str:
    timestamp = time.strftime("%Y_%m_%d-%H_%M_%S")
    return f"checkpoint_{timestamp}_iteration_{curr_iter}"


def _get_path_to_save(name: str, extension: str) -> PathLike:
    checkpoint_dir_path = get_checkpoint_dir_path()
    checkpoint_dir_path.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir_path.joinpath(f"{name}.{extension}")


def save_to_json(engine) -> None:
    logger.debug("STARTED: Saving checkpoint")
    data = {
        "top_coord": InitialValues.simulation_initial_parameters.area.max.latitude,
        "down_coord": InitialValues.simulation_initial_parameters.area.min.latitude,
        "left_coord": InitialValues.simulation_initial_parameters.area.min.longitude,
        "right_coord": InitialValues.simulation_initial_parameters.area.max.longitude,
        "time_range_start": str(InitialValues.simulation_initial_parameters.time.min),
        "time_range_end": str(InitialValues.simulation_initial_parameters.time.max),
        "data_time_step": int(InitialValues.simulation_initial_parameters.data_time_step.total_seconds() / 60),
        "cells_side_count_latitude": InitialValues.simulation_initial_parameters.interpolation_grid_size.latitude,
        "cells_side_count_longitude": InitialValues.simulation_initial_parameters.interpolation_grid_size.longitude,
        "point_side_size": InitialValues.point_side_size,
        "iter_as_sec": InitialValues.iter_as_sec,
        "min_oil_thickness": InitialValues.min_oil_thickness,
        "oil_viscosity": InitialValues.viscosity_kinematic,
        "oil_density": InitialValues.oil_density,
        "neighborhood": str(InitialValues.neighbourhood),
        "checkpoint_frequency": InitialValues.checkpoint_frequency,
        "total_simulation_time": engine.total_time,
        "curr_iter": int(engine.total_time / engine.timestep),
        "data_path": InitialValues.data_dir_path,
        "constant_sources": [_oil_source_to_dict(source) for source in engine.constant_sources],
        "points": [_point_to_dict(point) for point in engine.world.values()]
    }
    name = _get_name_to_save(int(engine.total_time / engine.timestep))
    with open(_get_path_to_save(name, "json"), "w") as file:
        json.dump(data, file, indent=4)

    engine.simulation_image.save(_get_path_to_save(name, "png"))

    logger.debug(f"Checkpoint saved fo file: {name}")


def load_from_json(path: str) -> dict[str, Any]:
    logger.debug(f"STARTED: Loading checkpoint from file: {path}")
    with open(path, "r") as file:
        data = json.load(file)
    constant_sources = []
    for source in data.get("constant_sources", []):
        coord = tuple(source["coord"])
        mass_per_minute = source["mass_per_minute"]
        spill_start = pd.Timestamp(source["spill_start"])
        spill_end = pd.Timestamp(source["spill_end"])
        constant_sources.append((coord, mass_per_minute, spill_start, spill_end))
    data["constant_sources"] = constant_sources
    logger.debug("FINISHED: Loading checkpoint")
    return data


def initialize_points_from_checkpoint(points: list[Any], engine):
    logger.debug("STARTED: Initializing points from checkpoint")
    world = {}
    for point_data in points:
        point_coord = tuple(point_data["coord"])
        point = Point(point_coord, engine)
        point.oil_mass = point_data["oil_mass"]
        point.evaporation_rate = point_data["evaporation_rate"]
        point.emulsification_rate = point_data["emulsification_rate"]
        point.viscosity_dynamic = point_data["viscosity_dynamic"]
        world[point_coord] = point
    logger.debug("FINISHED: Initializing points from checkpoint")
    engine.world = world
