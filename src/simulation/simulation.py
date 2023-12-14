from typing import Dict, List, Any

import pandas as pd

from checkpoints import save_to_json
from data.data_processor import DataProcessor
from data.measurment_data import Coordinates
from initial_values import InitialValues
from simulation.point import Point, Coord_t, TopographyState
from simulation.spreading import SpreadingEngine
from simulation.topology import load_topography, project_binary_map_coordinates


class SimulationEngine:
    def __init__(self, data_processor: DataProcessor):
        self._world: Dict[Coord_t, Point] = dict()
        self.spreading_engine = SpreadingEngine(self)

        Point.world = self._world
        self.data_processor = data_processor
        self.checkpoint_frequency = InitialValues.checkpoint_frequency
        self.timestep = InitialValues.iter_as_sec
        self._total_mass = 0
        self._total_land_mass = 0
        self.lands, self.x_indices, self.y_indices = load_topography()
        self._total_time = InitialValues.total_simulation_time
        self._constants_sources = []  # contains tuples (coord, mass_per_minute, spill_start, spill_end)

    def is_finished(self) -> bool:
        return self._total_time >= InitialValues.simulation_time

    def update(self, curr_iter: int) -> List[Coord_t]:
        self._pour_from_sources()
        self._update_oil_points()

        self._total_mass = 0
        self._total_land_mass = 0
        for point in self._world.values():
            point.pour_from_buffer()
            self._total_mass += point.oil_mass
            if point.topography == TopographyState.LAND:
                self._total_land_mass += point.oil_mass

        self.spreading_engine.spread_oil_points(self._total_mass)
        empty_points = [coord for coord, point in self._world.items() if not point.contain_oil()]
        deleted = []
        for point in empty_points:
            del self._world[point]
            deleted.append(point)
        self._total_time += self.timestep
        self.save_checkpoint(curr_iter)
        return deleted

    def _update_oil_points(self):
        for coord in list(self._world.keys()):  # copy because dict changes size during iteration
            self._world[coord].update()

    def add_oil_sources(self, oil_sources: List[dict[str, Any]]):
        for oil_source in oil_sources:
            coord = Coordinates(
                latitude=oil_source["coord"][0],
                longitude=oil_source["coord"][1]
            )
            goddamnit = project_binary_map_coordinates(coord)
            self._add_oil_source((goddamnit.latitude, goddamnit.longitude),
                                 oil_source["mass_per_minute"],
                                 oil_source["spill_start"],
                                 oil_source["spill_end"])

    def _add_oil_source(self, coord: Coord_t, mass_per_minute: float, spill_start: pd.Timestamp,
                        spill_end: pd.Timestamp):
        self._constants_sources.append((coord, mass_per_minute, spill_start, spill_end))

    def _pour_from_sources(self):
        current_timestamp = InitialValues.simulation_initial_parameters.time.min + pd.Timedelta(seconds=self._total_time)
        for spill in self._constants_sources:
            cords, mass_per_minute, spill_start, spill_end = spill
            if spill_start <= current_timestamp <= spill_end:
                if cords not in self._world and 0 <= cords[0] < InitialValues.point_side_lat_count and 0 <= cords[1] < InitialValues.point_side_lon_count:
                    self._world[cords] = Point(cords, self)
                self._world[cords].add_oil(mass_per_minute * self.timestep / 60)

    def get_topography(self, coord: Coord_t) -> TopographyState:
        if coord in self.lands:
            return TopographyState.LAND
        return TopographyState.SEA

    def get_oil_amounts(self):
        return self._total_mass - self._total_land_mass, self._total_land_mass

    def save_checkpoint(self, curr_iter: int, on_demand: bool = False):
        if on_demand or self.checkpoint_frequency > 0 and (self._total_time / self.timestep) % self.checkpoint_frequency == 0:
            save_to_json(self._world, self._total_time, curr_iter, self._constants_sources)

    @property
    def world(self):
        return self._world

    @world.setter
    def world(self, world: Dict[Coord_t, Point]):
        self._world = world
        Point.world = world

    @property
    def total_time(self):
        return self._total_time