import json
import time
from logging import getLogger
from os import PathLike
from typing import Dict, Any, List, Tuple

import pandas as pd

from files import get_checkpoint_dir_path
from initial_values import InitialValues
from simulation.point import Point, Coord_t, get_coordinate
from topology.binary_map_math import project_binary_map_coordinates_raw


logger = getLogger("checkpoints")


def _point_to_dict(point: Point) -> Dict[str, any]:
    coordinate = get_coordinate(point.coord)
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


def _oil_source_to_dict(source: Tuple[Coord_t, int, pd.Timestamp, pd.Timestamp]) -> Dict[str, any]:
    return {
        "coord": project_binary_map_coordinates_raw(source[0][0], source[0][1]),
        "mass_per_minute": source[1],
        "spill_start": str(source[2]),
        "spill_end": str(source[3])
    }


def _get_path_to_save(curr_iter: int) -> PathLike:
    timestamp = time.strftime("%Y_%m_%d-%H_%M_%S")
    checkpoint_dir_path = get_checkpoint_dir_path()
    checkpoint_dir_path.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir_path.joinpath(f"checkpoint_{timestamp}_iteration_{curr_iter}.json")

def save_to_json(world: Dict[Coord_t, Point], total_time: int, curr_iter: int, constant_sources: List[Tuple[Coord_t, int, pd.Timestamp, pd.Timestamp]]) -> None:
    logger.debug("STATED: Saving checkpoint")
    data = {
        "top_coord": InitialValues.simulation_initial_parameters.area.max.latitude,
        "down_coord": InitialValues.simulation_initial_parameters.area.min.latitude,
        "left_coord": InitialValues.simulation_initial_parameters.area.min.longitude,
        "right_coord": InitialValues.simulation_initial_parameters.area.max.longitude,
        "time_range_start": str(InitialValues.simulation_initial_parameters.time.min),
        "time_range_end": str(InitialValues.simulation_initial_parameters.time.min),
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
        "total_simulation_time": total_time,
        "curr_iter": curr_iter,
        "data_path": InitialValues.simulation_initial_parameters.path_to_data,

        "constants_sources": [_oil_source_to_dict(source) for source in constant_sources],
        "points": [_point_to_dict(point) for point in world.values()]
    }
    path = _get_path_to_save(curr_iter)
    with open(path, "w") as file:
        json.dump(data, file, indent=4)
    logger.debug(f"Checkpoint saved fo file: {path}")
        


def load_from_json(path: str) -> Dict[str, Any]:
    logger.debug(f"STATED: Loading checkpoint from file: {path}")
    with open(path, "r") as file:
        data = json.load(file)
    constants_sources = []
    for source in data.get("constants_sources", []):
        coord = tuple(source["coord"])
        mass_per_minute = source["mass_per_minute"]
        spill_start = pd.Timestamp(source["spill_start"])
        spill_end = pd.Timestamp(source["spill_end"])
        constants_sources.append((coord, mass_per_minute, spill_start, spill_end))
    data["constants_sources"] = constants_sources
    logger.debug("FINISHED: Loading checkpoint")
    return data


def initialize_points_from_checkpoint(points: List[Any], engine):
    logger.debug("STATED: Initializing points from checkpoint")
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
