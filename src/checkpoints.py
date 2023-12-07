import time

import pandas as pd

from simulation.point import Point, Coord_t
from constatnts import Constants as const
from files import get_main_path
from typing import Dict, Any, List, Tuple
import json


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
        "coord": source[0],
        "mass_per_minute": source[1],
        "spill_start": str(source[2]),
        "spill_end": str(source[3])
    }


def save_to_json(world: Dict[Coord_t, Point], total_time: int, constant_sources: List[Tuple[Coord_t, int, pd.Timestamp, pd.Timestamp]]) -> None:
    timestamp = time.strftime("%Y_%m_%d-%H_%M_%S")
    path = get_main_path().joinpath(f"checkpoints/checkpoint_{timestamp}.json")
    data = {
        "top_coord": const.simulation_initial_parameters.area.max.latitude,
        "down_coord": const.simulation_initial_parameters.area.min.latitude,
        "left_coord": const.simulation_initial_parameters.area.min.longitude,
        "right_coord": const.simulation_initial_parameters.area.max.longitude,
        "timestamp": str(const.simulation_initial_parameters.time.min + pd.Timedelta(seconds=total_time)),
        #TODO add more parameters
        "constants_sources": [oil_source_to_dict(source) for source in constant_sources],
        "points": [point_to_dict(point) for point in world.values()]
    }
    with open(path, "w") as file:
        json.dump(data, file, indent=4)

def load_from_json(name: str, initial_values, engine) -> Dict[str, Any]:
    path = get_main_path().joinpath(f"checkpoints/{name}")
    with open(path, "r") as file:
        data = json.load(file)
    world = {}
    for point_data in data["points"]:
        point_coord = tuple(point_data["coord"])
        point = Point(point_coord, initial_values, engine)
        point.oil_mass = point_data["oil_mass"]
        point.evaporation_rate = point_data["evaporation_rate"]
        point.emulsification_rate = point_data["emulsification_rate"]
        point.viscosity_dynamic = point_data["viscosity_dynamic"]
        world[point_coord] = point
    constants_sources = []
    for source in data.get("constants_sources", []):
        coord = tuple(source["coord"])
        mass_per_minute = source["mass_per_minute"]
        spill_start = pd.Timestamp(source["spill_start"])
        spill_end = pd.Timestamp(source["spill_end"])
        constants_sources.append((coord, mass_per_minute, spill_start, spill_end))
    data["constants_sources"] = constants_sources
    del data["points"]
    data["world"] = world
    return data