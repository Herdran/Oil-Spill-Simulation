import csv
import os
from math import exp, sqrt
from random import random as rand
from typing import Dict, Tuple, Set, List

import constatnts as const
from data.data_processor import DataProcessor
from point import Point, InitialValues, TopographyState


class SimulationEngine:
    def __init__(self, data_processor: DataProcessor):
        self.initial_values = InitialValues()
        self.world: Dict[Tuple[int, int], Point] = dict()

        Point.world = self.world
        self.spreading_pairs = self.generate_spreading_pairs()
        self.data_processor = data_processor
        self.total_mass = 0
        self.lands = self.load_topography()
        self.total_time = 0

    def is_finished(self):
        return self.total_time >= self.initial_values.time_limit

    def add_oil(self, x: int, y: int, mass: float):
        coord = (x, y)
        if coord not in self.world:
            self.world[coord] = Point(x, y, self.initial_values, self)
        self.world[coord].add_oil(mass)

    def update(self, delta_time) -> List[Tuple[int, int]]:
        self.update_oil_points(delta_time)

        self.total_mass = 0
        for point in self.world.values():
            point.pour_from_buffer()
            self.total_mass += point.oil_mass

        self.spread_oil_points(delta_time)

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

    def generate_spreading_pairs(self):
        return (
                [((x, y), (x + 1, y)) for x in range(0, const.POINTS_SIDE_COUNT - 1, 2) for y in
                 range(const.POINTS_SIDE_COUNT)]
                + [((x, y), (x + 1, y)) for x in range(1, const.POINTS_SIDE_COUNT - 1, 2) for y in
                   range(const.POINTS_SIDE_COUNT)]
                + [((x, y), (x, y + 1)) for y in range(0, const.POINTS_SIDE_COUNT - 1, 2) for x in
                   range(const.POINTS_SIDE_COUNT)]
                + [((x, y), (x, y + 1)) for y in range(1, const.POINTS_SIDE_COUNT - 1, 2) for x in
                   range(const.POINTS_SIDE_COUNT)]
        )

    def spread_oil_points(self, delta_time: float):
        for pair in self.spreading_pairs:
            first, second = pair
            if first not in self.world and second not in self.world:
                continue
            if first not in self.world:
                self.world[first] = Point(first[0], first[1], self.initial_values, self)
            if second not in self.world:
                self.world[second] = Point(second[0], second[1], self.initial_values, self)
            self.process_spread_between(delta_time, self.from_coords(first), self.from_coords(second))

    def process_spread_between(self, delta_time: float, first: Point, second: Point) -> None:
        if not (first.topography == TopographyState.SEA and second.topography == TopographyState.SEA):
            return

        length = const.POINT_SIDE_SIZE
        V = self.total_mass / self.initial_values.density
        g = 9.8
        delta = (self.initial_values.water_density - self.initial_values.density) / self.initial_values.water_density
        viscosity = 10e-6
        D = 0.49 / self.initial_values.propagation_factor * (V ** 2 * g * delta / sqrt(viscosity)) ** (1 / 3) / sqrt(
            delta_time)
        delta_mass = 0.5 * (second.oil_mass - first.oil_mass) * (1 - exp(-2 * D / (length ** 2) * delta_time))

        if delta_mass == 0:
            return
        elif delta_mass < 0:
            ratio = delta_mass / -first.oil_mass
            from_cell = first
            to_cell = second
        else:
            ratio = delta_mass / second.oil_mass
            from_cell = second
            to_cell = first

        real_delta = rand() * ratio * from_cell.oil_mass
        from_cell.oil_mass -= real_delta
        to_cell.viscosity = (to_cell.viscosity * to_cell.oil_mass + from_cell.viscosity * real_delta) / (
                to_cell.oil_mass + real_delta)
        to_cell.emulsification_rate = (
                                              to_cell.emulsification_rate * to_cell.oil_mass + from_cell.emulsification_rate * real_delta) / (
                                              to_cell.oil_mass + real_delta)
        to_cell.oil_mass += real_delta

    def from_coords(self, coord) -> Point:
        return self.world[coord]

    def load_topography(self) -> Set[Tuple[int, int]]:
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

    def get_topography(self, x, y):
        if (x, y) in self.lands:
            return TopographyState.LAND
        return TopographyState.SEA
