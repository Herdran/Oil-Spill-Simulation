from math import exp, sqrt
from random import shuffle

from initial_values import InitialValues
from simulation.point import Point, Coord_t, TopographyState, is_coord_in_simulation_area
from simulation.utilities import get_neighbour_coordinates


class SpreadingEngine:
    def __init__(self, engine):
        self._engine = engine

    def spread_oil_points(self, total_mass: float):
        new_points = {}
        for coord, point in self._engine.world.items():
            x, y = coord
            neighbours = get_neighbour_coordinates(x, y, InitialValues.neighbourhood)
            shuffle(neighbours)
            for neighbour in neighbours:
                if neighbour not in self._engine.world:
                    neighbour_point = self.new_point(neighbour, new_points)
                    _process_spread_between(total_mass, point, neighbour_point, True)
                else:
                    neighbour_point = self._engine.world[neighbour]
                    _process_spread_between(total_mass, point, neighbour_point, False)
        self._update_new_points(new_points)
        for point in self._engine.world.values():
            point.pour_from_buffer()

    def new_point(self, coord: Coord_t, new_points: dict[Coord_t, Point]) -> Point:
        if coord in new_points:
            return new_points[coord]
        point = Point(coord, self._engine)
        new_points[coord] = point
        return point

    def _update_new_points(self, new_points: dict[Coord_t, Point]) -> None:
        for coord, point in new_points.items():
            if not is_coord_in_simulation_area(coord):
                continue
            self._engine.world[coord] = point


def _process_spread_between(total_mass: float, first: Point, second: Point, is_new: bool) -> None:
    if not (first.topography == TopographyState.SEA and second.topography == TopographyState.SEA):
        return

    length = InitialValues.point_side_size
    V = total_mass / InitialValues.oil_density
    G = 9.8
    delta = (InitialValues.water_density - InitialValues.oil_density) / InitialValues.water_density
    dynamic_viscosity = (first.viscosity_dynamic + second.viscosity_dynamic) / 2
    kinematic_viscosity = dynamic_viscosity / InitialValues.oil_density
    D = 0.48 / InitialValues.propagation_factor * (V ** 2 * G * delta / sqrt(kinematic_viscosity)) ** (
                1 / 3) / sqrt(
        InitialValues.iter_as_sec)
    delta_mass = 0.5 * (second.oil_mass - first.oil_mass) * (
                1 - exp(-2 * D / (length ** 2) * InitialValues.iter_as_sec))
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

    real_delta = ratio * from_cell.oil_mass
    from_cell.oil_mass -= real_delta
    to_cell.oil_buffer.append((real_delta, from_cell.viscosity_dynamic, from_cell.emulsification_rate))
