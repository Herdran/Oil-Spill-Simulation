import csv
import os
from typing import Dict, Set, List

from data.data_processor import DataProcessor
from simulation.point import Point, Coord_t, InitialValues, TopographyState
from simulation.spreading import Spreading_engine

class SimulationEngine:
    def __init__(self, data_processor: DataProcessor):
        self.initial_values = InitialValues()
        self.world: Dict[Coord_t, Point] = dict()
        self.spreading_engine = Spreading_engine(self)

        Point.world = self.world
        self.data_processor = data_processor
        self.total_mass = 0
        self.lands = self.load_topography()
        self.total_time = 0

    def is_finished(self) -> bool:
        return self.total_time >= self.initial_values.time_limit

    def update(self, delta_time) -> List[Coord_t]:
        self.update_oil_points(delta_time)

        self.total_mass = 0
        for point in self.world.values():
            point.pour_from_buffer()
            self.total_mass += point.oil_mass

        self.spreading_engine.spread_oil_points(self.total_mass, delta_time)

        empty_points = [coord for coord, point in self.world.items() if not point.contain_oil()]
        deleted = []
        for point in empty_points:
            del self.world[point]
            deleted.append(point)
        self.total_time += delta_time
        return deleted

    def update_oil_points(self, delta_time):
        for coord in list(self.world.keys()):  # copy because dict changes size during iteration
            self.world[coord].update(delta_time)
        
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