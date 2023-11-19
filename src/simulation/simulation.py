import csv
from typing import Dict, Set, List

from data.data_processor import DataProcessor
from simulation.point import Point, Coord_t, InitialValues, TopographyState
from simulation.spreading import SpreadingEngine
from simulation.utilities import Neighbourhood
from files import get_main_path
import constatnts as const

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

    def is_finished(self) -> bool:
        return self.total_time >= const.SIMULATION_TIME

    def update(self, delta_time) -> List[Coord_t]:
        self.points_changed = []
        self.update_oil_points(delta_time)

        self.total_mass = 0
        self.total_land_mass = 0
        for point in self.world.values():
            point.pour_from_buffer()
            self.total_mass += point.oil_mass
            if(point.topography == TopographyState.LAND):
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

    def load_topography(self) -> Set[Coord_t]:
        # TODO!!!!! <- path need to be selected by GUI
        lands = set()
        path = get_main_path().joinpath('data/topography.csv')
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
