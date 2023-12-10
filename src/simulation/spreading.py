from math import exp, sqrt
from random import random as rand
from random import shuffle
from typing import Dict

from constatnts import Constants as const
from simulation.point import Point, Coord_t, TopographyState
from simulation.utilities import get_neighbour_coordinates


class SpreadingEngine:
    def __init__(self, engine):
        self.world = engine.world
        self.engine = engine

    def spread_oil_points(self, total_mass: float):
        new_points = {}
        for coord, point in self.world.items():
            x, y = coord
            neighbours = get_neighbour_coordinates(x, y, const.neighbourhood)
            shuffle(neighbours)
            for neighbour in neighbours:
                if not (0 <= neighbour[0] < const.point_side_count and 0 <= neighbour[1] < const.point_side_count):
                    continue
                if neighbour not in self.world:
                    neighbour_point = self.new_point(neighbour, new_points)
                    self.process_spread_between(total_mass, point, neighbour_point, True)
                else:
                    neighbour_point = self.world[neighbour]
                    self.process_spread_between(total_mass, point, neighbour_point, False)
        self.update_new_points(new_points)
        for point in self.world.values():
            point.pour_from_buffer()

    def new_point(self, coord: Coord_t, new_points: Dict[Coord_t, Point]) -> Point:
        if coord in new_points:
            return new_points[coord]
        point = Point(coord, self.engine)
        new_points[coord] = point
        return point

    def update_new_points(self, new_points: Dict[Coord_t, Point]) -> None:
        for coord, point in new_points.items():
            if not (0 <= coord[0] < const.point_side_count and 0 <= coord[1] < const.point_side_count):
                continue
            self.world[coord] = point
            self.engine.points_changed.append(coord)

    def process_spread_between(self, total_mass: float, first: Point, second: Point, is_new: bool) -> None:
        if not (first.topography == TopographyState.SEA and second.topography == TopographyState.SEA):
            return
          
        length = const.point_side_size
        V = total_mass / const.oil_density
        G = 9.8
        delta = (const.water_density - const.oil_density) / const.water_density
        dynamic_viscosity = (first.viscosity_dynamic + second.viscosity_dynamic) / 2
        kinematic_viscosity = dynamic_viscosity / const.oil_density
        D = 0.48 / const.propagation_factor * (V ** 2 * G * delta / sqrt(kinematic_viscosity)) ** (1 / 3) / sqrt(
            const.iter_as_sec)
        delta_mass = 0.5 * (second.oil_mass - first.oil_mass) * (1 - exp(-2 * D / (length ** 2) * const.iter_as_sec))
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
        to_cell.oil_buffer.append((real_delta, from_cell.viscosity_dynamic, from_cell.emulsification_rate))
