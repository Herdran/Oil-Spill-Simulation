import csv
import os
from typing import Dict, Set, List

import pandas as pd

from data.data_processor import DataProcessor
from simulation.point import Point, Coord_t, InitialValues, TopographyState
from simulation.spreading import SpreadingEngine
from simulation.utilities import Neighbourhood
from constatnts import SIMULATION_INITIAL_PARAMETERS


class SimulationEngine:
    def __init__(self, data_processor: DataProcessor, neighbourhood: Neighbourhood = Neighbourhood.MOORE):
        self.initial_values = InitialValues(neighbourhood)
        self.world: Dict[Coord_t, Point] = dict()
        self.spreading_engine = SpreadingEngine(self)

        Point.world = self.world
        self.data_processor = data_processor
        self.total_mass = 0
        self.total_land_mass = 0
        self.lands = self.load_topography()
        self.total_time = 0
        self.points_changed = []
        self._constants_sources = []

    def is_finished(self) -> bool:
        return self.total_time >= self.initial_values.time_limit

    def update(self, delta_time) -> List[Coord_t]:
        self.points_changed = []
        self.pour_from_sources(delta_time)
        self.update_oil_points(delta_time)

        self.total_mass = 0
        self.total_land_mass = 0
        for point in self.world.values():
            point.pour_from_buffer()
            self.total_mass += point.oil_mass
            if point.topography == TopographyState.LAND:
                self.total_land_mass += point.oil_mass

        self.spreading_engine.spread_oil_points(self.total_mass, delta_time)

        empty_points = [coord for coord, point in self.world.items() if not point.contain_oil()]
        deleted = []
        for point in empty_points:
            del self.world[point]
            deleted.append(point)
            self.points_changed.append(point)
        self.total_time += delta_time
        return deleted

    def update_oil_points(self, delta_time):
        for coord in list(self.world.keys()):  # copy because dict changes size during iteration
            self.world[coord].update(delta_time)

    def add_oil_source(self, coord: Coord_t, mass_per_minute: float, spill_start: pd.Timestamp,
                       spill_end: pd.Timestamp):
        self._constants_sources.append((coord, mass_per_minute, spill_start, spill_end))

    def pour_from_sources(self, delta_seconds: float):
        current_timestamp = SIMULATION_INITIAL_PARAMETERS.time.min + pd.Timedelta(seconds=self.total_time)
        for spill in self._constants_sources:
            cords, mass_per_minute, spill_start, spill_end = spill
            if spill_start <= current_timestamp <= spill_end:
                if cords not in self.world:
                    self.world[cords] = Point(cords, self.initial_values, self)
                    self.points_changed.append(cords)
                self.world[cords].add_oil(mass_per_minute * delta_seconds / 60)

    def load_topography(self) -> Set[Coord_t]:
        # TODO!!!!! <- path need to be selected by GUI
        lands = set()
        path = 'data/topography.csv'
        if os.getcwd().endswith('src'):
            path = '../' + path
        with open(path, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            for y, row in enumerate(reader):
                for x, state in enumerate(row):
                    if state == '1':
                        lands.add((x, y))
        return lands

    def get_topography(self, coord: Coord_t) -> TopographyState:
        if coord in self.lands:
            return TopographyState.LAND
        return TopographyState.SEA

    def get_oil_amounts(self):
        return self.total_mass - self.total_land_mass, self.total_land_mass