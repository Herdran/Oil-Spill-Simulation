from math import exp, sqrt
from random import random as rand
from random import shuffle
from typing import Dict

import constatnts as const
from simulation.point import Point, Coord_t, TopographyState
from simulation.utilities import get_neighbour_coordinates


class SpreadingEngine:
    def __init__(self, engine):
        self.initial_values = engine.initial_values
        self.world = engine.world
        self.engine = engine

    def spread_oil_points(self, total_mass: float, delta_time: float):
        new_points = {}
        for coord, point in self.world.items():
            x, y = coord
            neighbours = get_neighbour_coordinates(x, y, self.initial_values.neighbourhood)
            shuffle(neighbours)
            for neighbour in neighbours:
                if not (0 <= neighbour[0] < const.POINTS_SIDE_COUNT and 0 <= neighbour[1] < const.POINTS_SIDE_COUNT):
                    continue
                if neighbour not in self.world:
                    neighbour_point = self.new_point(neighbour, new_points)
                    self.process_spread_between(total_mass, delta_time, point, neighbour_point, True)
                else:
                    neighbour_point = self.world[neighbour]
                    self.process_spread_between(total_mass, delta_time, point, neighbour_point, False)
        self.world.update(new_points)
        for point in self.world.values():
            point.pour_from_buffer()

    def new_point(self, coord: Coord_t, new_points: Dict[Coord_t, Point]) -> Point:
        if coord in new_points:
            return new_points[coord]
        point = Point(coord, self.initial_values, self.engine)
        new_points[coord] = point
        return point

    def process_spread_between(self, total_mass: float, delta_time: float, first: Point, second: Point, is_new: bool) -> None:
        if not (first.topography == TopographyState.SEA and second.topography == TopographyState.SEA):
            return

        length = const.POINT_SIDE_SIZE
        V = total_mass / self.initial_values.density
        G = 9.8
        delta = (self.initial_values.water_density - self.initial_values.density) / self.initial_values.water_density
        viscosity = 10e-6
        D = 0.49 / self.initial_values.propagation_factor * (V ** 2 * G * delta / sqrt(viscosity)) ** (1 / 3) / sqrt(
            delta_time)
        delta_mass = 0.5 * (second.oil_mass - first.oil_mass) * (1 - exp(-2 * D / (length ** 2) * delta_time))
        if not is_new:
            delta_mass = delta_mass / 2  # due to double spreading on the same pair

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
        to_cell.oil_buffer.append((real_delta, from_cell.viscosity, from_cell.emulsification_rate))
