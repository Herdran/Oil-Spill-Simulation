from typing import Dict
from math import exp, sqrt
from random import random as rand

from simulation.point import InitialValues, Point, Coord_t, TopographyState
import constatnts as const


SPREADING_PAIRS_FILTERS = [
    lambda coord: coord[0] % 2 == 0,
    lambda coord: coord[0] % 2 == 1,
    lambda coord: coord[1] % 2 == 0,
    lambda coord: coord[1] % 2 == 1,
]

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
    
    def spread_oil_points(self, total_mass, delta_time: float):
        for spreading_turn in range(len(SPREADING_PAIRS_FILTERS)):
            new_points = {}
            for key in self.world.keys():
                if SPREADING_PAIRS_FILTERS[spreading_turn](key):
                    second = spreading_next(spreading_turn, key)
                    if second not in self.world:
                        second_point = self.new_point(second)
                        new_points[second] = second_point
                    else:
                        second_point = self.world[second]
                    self.process_spread_between(total_mass, delta_time, self.world[key], second_point) 
                    continue
                prev = spreading_prev(spreading_turn, key)
                if prev not in self.world:
                    prev_point = self.new_point(prev)
                    new_points[prev] = prev_point
                    self.process_spread_between(total_mass, delta_time, prev_point, self.world[key])
            self.world.update(new_points)
    
    def process_spread_between(self, total_mass: float, delta_time: float, first: Point, second: Point) -> None:
        if not (first.topography == TopographyState.SEA and second.topography == TopographyState.SEA):
            return

        length = const.POINT_SIDE_SIZE
        V = total_mass / self.initial_values.density
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
        
    def new_point(self, coord: Coord_t) -> Point:
        return Point(coord, self.initial_values, self.engine)
