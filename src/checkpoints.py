import json
import time
from typing import Dict, Any, List, Tuple

import pandas as pd

from files import get_main_path
from initial_values import InitialValues
from simulation.point import Point, Coord_t
from simulation.topology import project_coordinates_oil_sources_from_simulation


def point_to_dict(point: Point) -> Dict[str, any]:
    return {
        "coord": point.coord,
        "coordinates": {
            "latitude": point.coordinates.latitude,
            "longitude": point.coordinates.longitude
        },
        "oil_mass": point.oil_mass,
        "evaporation_rate": point.evaporation_rate,
        "emulsification_rate": point.emulsification_rate,
        "viscosity_dynamic": point.viscosity_dynamic
    }


def oil_source_to_dict(source: Tuple[Coord_t, int, pd.Timestamp, pd.Timestamp]) -> Dict[str, any]:
    return {
        "coord": project_coordinates_oil_sources_from_simulation(source[0]),
        "mass_per_minute": source[1],
        "spill_start": str(source[2]),
        "spill_end": str(source[3])
    }


def save_to_json(world: Dict[Coord_t, Point], total_time: int, curr_iter: int, constant_sources: List[Tuple[Coord_t, int, pd.Timestamp, pd.Timestamp]]) -> None:
    timestamp = time.strftime("%Y_%m_%d-%H_%M_%S")
    path = get_main_path().joinpath(f"checkpoints/checkpoint_{timestamp}.json")
    data = {
        "top_coord": InitialValues.simulation_initial_parameters.area.max.latitude,
        "down_coord": InitialValues.simulation_initial_parameters.area.min.latitude,
        "left_coord": InitialValues.simulation_initial_parameters.area.min.longitude,
        "right_coord": InitialValues.simulation_initial_parameters.area.max.longitude,
        "time_range_start": str(InitialValues.simulation_initial_parameters.time.min),
        "time_range_end": str(InitialValues.simulation_initial_parameters.time.min),
        "data_time_step": int(InitialValues.simulation_initial_parameters.data_time_step.total_seconds() / 60),
        "cells_side_count_latitude": InitialValues.simulation_initial_parameters.cells_side_count.latitude,
        "cells_side_count_longitude": InitialValues.simulation_initial_parameters.cells_side_count.longitude,
        "point_side_size": InitialValues.point_side_size,
        "iter_as_sec": InitialValues.iter_as_sec,
        "min_oil_thickness": InitialValues.min_oil_thickness,
        "oil_viscosity": InitialValues.viscosity_kinematic,
        "oil_density": InitialValues.oil_density,
        "neighborhood": str(InitialValues.neighbourhood),
        "checkpoint_frequency": InitialValues.checkpoint_frequency,
        "total_simulation_time": total_time,
        "curr_iter": curr_iter,

        "constants_sources": [oil_source_to_dict(source) for source in constant_sources],
        "points": [point_to_dict(point) for point in world.values()]
    }
    with open(path, "w") as file:
        json.dump(data, file, indent=4)


def load_from_json(path: str) -> Dict[str, Any]:
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
    return data


def initialize_points_from_checkpoint(points: List[Any], engine):
    world = {}
    for point_data in points:
        point_coord = tuple(point_data["coord"])
        point = Point(point_coord, engine)
        point.oil_mass = point_data["oil_mass"]
        point.evaporation_rate = point_data["evaporation_rate"]
        point.emulsification_rate = point_data["emulsification_rate"]
        point.viscosity_dynamic = point_data["viscosity_dynamic"]
        world[point_coord] = point

    engine.set_world(world)
