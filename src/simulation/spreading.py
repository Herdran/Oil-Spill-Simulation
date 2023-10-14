from math import exp, sqrt
from random import random as rand
from typing import Dict, Optional

import constatnts as const
from simulation.point import Point, Coord_t, TopographyState

'''
There are 4 spreading turns. Each turn is responsible for spreading oil with neighbour in one direction.
Here is a filter thet check if the point is the first ponit of spreading pair (is left or top of the pair).

So for example if points are:
00 01 02 03
10 11 12 13
20 21 22 23

at first turn processed points are: (00, 01), (02, 03), (10, 11)...
at second: (01, 02), (11, 12), (21, 22)...
at third: (00, 10), (01, 11), (02, 12) ...
at fourth: (10, 20), (11, 21), (12, 22)...
'''
SPREADING_PAIRS_FILTERS = [
    lambda coord: coord[0] % 2 == 0,
    lambda coord: coord[0] % 2 == 1,
    lambda coord: coord[1] % 2 == 0,
    lambda coord: coord[1] % 2 == 1,
]

'''
Offset of the second point of spreading pair from the first one.
'''
SPREADING_NEXT = [
    (1, 0),
    (1, 0),
    (0, 1),
    (0, 1),
]


def spreading_next(turn: int, coord: Coord_t) -> Coord_t:
    return coord[0] + SPREADING_NEXT[turn][0], coord[1] + SPREADING_NEXT[turn][1]


def spreading_prev(turn: int, coord: Coord_t) -> Coord_t:
    return coord[0] - SPREADING_NEXT[turn][0], coord[1] - SPREADING_NEXT[turn][1]


class Spreading_engine:
    def __init__(self, engine):
        self.initial_values = engine.initial_values
        self.world = engine.world
        self.engine = engine

    def spread_oil_points(self, total_mass: float, delta_time: float):
        for spreading_turn in range(len(SPREADING_PAIRS_FILTERS)):
            new_points = {}
            for coord in self.world.keys():
                if SPREADING_PAIRS_FILTERS[spreading_turn](coord):
                    second_point = self.get_spreading_next(spreading_turn, new_points, coord)
                    if second_point is not None:
                        self.process_spread_between(total_mass, delta_time, self.world[coord], second_point)
                else:
                    prev = spreading_prev(spreading_turn, coord)
                    if not (0 <= prev[0] < const.POINTS_SIDE_COUNT and 0 <= prev[1] < const.POINTS_SIDE_COUNT):
                        continue
                    if prev not in self.world:
                        prev_point = self.new_point(prev, new_points)
                        self.process_spread_between(total_mass, delta_time, prev_point, self.world[coord])
            self.world.update(new_points)

    def get_spreading_next(self, spreading_turn: int, new_points: Dict[Coord_t, Point], coord: Coord_t) ->\
            Optional[Point]:
        second = spreading_next(spreading_turn, coord)
        if not (0 <= second[0] < const.POINTS_SIDE_COUNT and 0 <= second[1] < const.POINTS_SIDE_COUNT):
            return None
        if second in self.world:
            return self.world[second]
        return self.new_point(second, new_points)

    def new_point(self, coord: Coord_t, new_points: Dict[Coord_t, Point]) -> Point:
        point = Point(coord, self.initial_values, self.engine)
        self.engine.points_changed.append(coord)
        new_points[coord] = point
        return point

    def process_spread_between(self, total_mass: float, delta_time: float, first: Point, second: Point) -> None:
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
