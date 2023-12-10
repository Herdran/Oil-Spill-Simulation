from typing import Dict, List, Any

import pandas as pd

from data.data_processor import DataProcessor
from simulation.point import Point, Coord_t, TopographyState
from simulation.spreading import SpreadingEngine
from simulation.topology import load_topography, project_coordinates_oil_sources
from checkpoints import save_to_json
from constatnts import Constants as const


class SimulationEngine:
    def __init__(self, data_processor: DataProcessor, checkpoint_frequency: int = 0):
        self.world: Dict[Coord_t, Point] = dict()
        self.spreading_engine = SpreadingEngine(self)

        Point.world = self.world
        self.data_processor = data_processor
        self.checkpoint_frequency = checkpoint_frequency  #TODO move to constants
        self.timestep = const.iter_as_sec
        self.total_mass = 0
        self.total_land_mass = 0
        self.lands = load_topography()
        self.total_time = 0
        self.points_changed = []
        self._constants_sources = []  # contains tuples (coord, mass_per_minute, spill_start, spill_end)

    def is_finished(self) -> bool:
        return self.total_time >= const.simulation_time

    def update(self) -> List[Coord_t]:
        self.points_changed = []
        self.pour_from_sources()
        self.update_oil_points()

        self.total_mass = 0
        self.total_land_mass = 0
        for point in self.world.values():
            point.pour_from_buffer()
            self.total_mass += point.oil_mass
            if point.topography == TopographyState.LAND:
                self.total_land_mass += point.oil_mass

        self.spreading_engine.spread_oil_points(self.total_mass)
        empty_points = [coord for coord, point in self.world.items() if not point.contain_oil()]
        deleted = []
        for point in empty_points:
            del self.world[point]
            deleted.append(point)
            self.points_changed.append(point)
        self.total_time += self.timestep
        self._save_checkpoint()
        return deleted

    def update_oil_points(self):
        for coord in list(self.world.keys()):  # copy because dict changes size during iteration
            self.world[coord].update()

    def add_oil_sources(self, oil_sources: List[dict[str, Any]]):
        for oil_source in oil_sources:
            self.add_oil_source(project_coordinates_oil_sources(oil_source["coord"]),
                                oil_source["mass_per_minute"],
                                oil_source["spill_start"],
                                oil_source["spill_end"])

    def add_oil_source(self, coord: Coord_t, mass_per_minute: float, spill_start: pd.Timestamp,
                       spill_end: pd.Timestamp):
        self._constants_sources.append((coord, mass_per_minute, spill_start, spill_end))

    def pour_from_sources(self):
        current_timestamp = const.simulation_initial_parameters.time.min + pd.Timedelta(seconds=self.total_time)
        for spill in self._constants_sources:
            cords, mass_per_minute, spill_start, spill_end = spill
            if spill_start <= current_timestamp <= spill_end:
                if cords not in self.world:
                    self.world[cords] = Point(cords, self)
                    self.points_changed.append(cords)
                self.world[cords].add_oil(mass_per_minute * self.timestep / 60)

    def get_topography(self, coord: Coord_t) -> TopographyState:
        if coord in self.lands:
            return TopographyState.LAND
        return TopographyState.SEA

    def get_oil_amounts(self):
        return self.total_mass - self.total_land_mass, self.total_land_mass

    def _save_checkpoint(self):
        if self.checkpoint_frequency > 0 and (self.total_time / self.timestep) % self.checkpoint_frequency == 0:
            save_to_json(self.world, self.total_time, self._constants_sources)

    def set_world(self, world: Dict[Coord_t, Point]):
        self.world = world
        Point.world = world