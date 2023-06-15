import csv
import os
from enum import Enum
from math import exp, log, sqrt, isnan
from random import random as rand

import numpy as np

import water_current_data
from constatnts import *


class TopographyState(Enum):
    LAND = 0
    SEA = 1


total_time = 0


class InitialValues:
    def __init__(self):
        self.water_density = 997  # [kg/m^3]
        self.density = 835  # [kg/m^3]
        self.viscosity = 10
        self.surface_tension = 30  # [dyne/s]
        self.time_limit = 24 * 60 * 60  # [s]
        self.emulsion_max_content_water = 0.7  # max content of water in the emulsion
        self.molar_mass = 348.23  # [g/mol] mean
        self.boiling_point = 609  # [K] mean
        self.interfacial_tension = 30  # [dyna/cm]
        self.propagation_factor = 2.5
        self.c = 0.7  # constant from paper
        self.emulsification_rate = 0.01


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.latitude = CELL_LAT[y]
        self.longitude = CELL_LON[x]
        self.wind_velocity = np.array([2.08753, -3.54677])
        self.temperature = 302.15  # [K]

        self.default_wave_velocity = np.array([0.0, 0.0])

        self.water_current_data = None
        self.times = None

    def get_wave_velocity(self):
        if self.water_current_data is None or self.times is None:
            return self.default_wave_velocity

        # temp
        return np.array([self.water_current_data[int(total_time / 3600) % 13].v,
                         self.water_current_data[int(total_time / 3600) % 13].u])


class Point:
    world = []

    def __init__(self, x, y, initial_values: InitialValues, cell: Cell):
        self.topography = TopographyState.SEA
        self.x = x
        self.y = y
        self.cell = cell
        self.oil_mass = 0  # [kg]
        self.initial_values = initial_values
        self.emulsification_rate = initial_values.emulsification_rate
        self.viscosity = initial_values.viscosity  # [cP]
        self.oil_buffer = []  # contains tuples (mass, viscosity, emulsification_rate)
        self.advection_buffer = np.array([0, 0], dtype='f')
        self.evaporation_rate = 0
        self.change_occurred = True  # TODO to be set when point is updated

    def contain_oil(self) -> bool:
        return self.oil_mass > 0

    def add_oil(self, mass: float) -> None:
        # maybe initial emulsification rate will be changed
        self.emulsification_rate = (self.oil_mass * self.emulsification_rate +
                                    mass * self.initial_values.emulsification_rate) / (self.oil_mass + mass)
        self.viscosity = (self.oil_mass * self.viscosity + mass * self.initial_values.viscosity) / (
                self.oil_mass + mass)
        self.oil_mass += mass

    def update(self, delta_time: float) -> None:
        if self.topography == TopographyState.LAND:
            self.process_seashore_interaction(delta_time)
            return
        delta_y = self.process_emulsification(delta_time)
        delta_f = self.process_evaporation(delta_time)
        self.process_natural_dispersion(delta_time)
        self.viscosity_change(delta_f, delta_y)

        # to na końcu na pewno
        self.process_advection(delta_time)

    def process_emulsification(self, delta_time: float) -> float:
        K = 2.0e-6
        old_emulsification_rate = self.emulsification_rate
        self.emulsification_rate += delta_time * K * (
                ((np.linalg.norm(self.cell.wind_velocity) + 1) ** 2) * (
                1 - self.emulsification_rate / self.initial_values.c))
        if self.emulsification_rate > self.initial_values.emulsion_max_content_water:
            self.emulsification_rate = self.initial_values.emulsion_max_content_water
        return self.emulsification_rate - old_emulsification_rate

    def process_evaporation(self, delta_time: float) -> float:
        K = 1.25e-3
        P = 1000 * exp(-(4.4 + log(self.initial_values.boiling_point)) * (
                1.803 * (self.initial_values.boiling_point / self.cell.temperature - 1) - 0.803 * log(
            self.initial_values.boiling_point / self.cell.temperature)))  # [Pa]
        R = 8.314  # [J/(mol*K)]

        self.evaporation_rate = (K * (self.initial_values.molar_mass / 1000) * P) / (R * self.cell.temperature)
        delta_mass = -1 * min(delta_time * POINT_SIDE_SIZE * POINT_SIDE_SIZE * self.evaporation_rate, self.oil_mass)
        delta_f = -delta_mass / self.oil_mass
        self.oil_mass += delta_mass
        return delta_f

    def process_seashore_interaction(self, delta_time: float) -> None:
        half_time = 3600 * 24  # 24h for sand beach / sand and gravel beach
        delta_mass = log(2) * self.oil_mass * delta_time / half_time
        self.oil_mass -= delta_mass
        to_share = []
        for cords in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            if not ((0 <= self.x + cords[0] < WORLD_SIDE_SIZE) and (0 <= self.y + cords[1] < WORLD_SIDE_SIZE)):
                continue
            neighbor = self.world[self.x + cords[0]][self.y + cords[1]]
            if neighbor.topography == TopographyState.SEA:
                to_share.append(neighbor)
        if len(to_share) == 0:  # in case of bug
            return
        delta_mass /= len(to_share)
        for neighbor in to_share:
            neighbor.oil_mass += delta_mass

    def into_min_max(self, x, y):
        return [
            [x - 0.5, y - 0.5],
            [x + 0.5, y + 0.5],
        ]

    def process_advection(self, delta_time: float) -> None:
        alpha = 1.1
        beta = 0.03
        delta_r = (alpha * self.cell.get_wave_velocity() + beta * self.cell.wind_velocity) * delta_time
        delta_r /= POINT_SIDE_SIZE

        # buffering how far oil went in time step
        self.advection_buffer += delta_r
        next_x = self.x + int(self.advection_buffer[0])
        next_y = self.y + int(self.advection_buffer[1])
        if 0 <= next_x < WORLD_SIDE_SIZE and 0 <= next_y < WORLD_SIDE_SIZE:
            self.world[next_x][next_y].oil_buffer.append((self.oil_mass, self.viscosity, self.emulsification_rate))
            self.advection_buffer -= np.array([next_x - self.x, next_y - self.y])
        self.oil_mass = 0

    def process_natural_dispersion(self, delta_time: float) -> None:
        Da = 0.11 * (np.linalg.norm(self.cell.wind_velocity) + 1) ** 2
        interfacial_tension = self.initial_values.interfacial_tension * (1 + self.evaporation_rate)
        Db = 1 / (1 + 50 * sqrt(self.viscosity) * self.slick_thickness() * interfacial_tension)
        self.oil_mass -= self.oil_mass * Da * Db / (3600 * delta_time)

    def slick_thickness(self) -> float:
        thickness = (self.oil_mass / self.initial_values.density) / (POINT_SIDE_SIZE ** 2)  # [m]
        return thickness / 100  # [cm]

    def viscosity_change(self, delta_F: float, delta_Y: float) -> None:
        C2 = 10
        delta_viscosity = C2 * self.viscosity * delta_F + (2.5 * self.viscosity * delta_Y) / (
                (1 - self.initial_values.emulsion_max_content_water * self.emulsification_rate) ** 2)
        self.viscosity += delta_viscosity
        if self.oil_mass < 1:
            self.viscosity = self.initial_values.viscosity

    def pour_from_buffer(self):
        # nie uwzględniamy masy w punkcie, bo wszystko powinno być w buforze
        oil_mass = sum([tup[0] for tup in self.oil_buffer])
        if oil_mass < 1:
            return
        self.viscosity = sum([tup[0] * tup[1] for tup in self.oil_buffer]) / oil_mass
        self.emulsification_rate = sum([tup[0] * tup[2] for tup in self.oil_buffer]) / oil_mass
        self.oil_buffer = []
        self.oil_mass = oil_mass


class SimulationEngine:
    def __init__(self):
        self.initial_values = InitialValues()
        self.cells = [[Cell(x, y) for y in range(GRID_SIDE_SIZE)]
                      for x in range(GRID_SIDE_SIZE)]
        self.world = [[Point(x, y, self.initial_values, self.cells[x // CELL_SIDE_SIZE][y // CELL_SIDE_SIZE])
                       for y in range(WORLD_SIDE_SIZE)]
                      for x in range(WORLD_SIDE_SIZE)]

        Point.world = self.world
        self.spreading_pairs = self.generate_spreading_pairs()

        self.current_oil_volume = 100

    def start(self, preset_path=None):
        self.load_topography()
        self.load_water_current_data()

    def load_water_current_data(self):
        stations, times, data = water_current_data.get_data()
        for cell_row in self.cells:
            for cell in cell_row:
                station_id = water_current_data.get_nearest_station(stations, cell.latitude, cell.longitude)
                cell.water_current_data = data[station_id]
                cell.times = times

    def is_finished(self):
        return total_time >= self.initial_values.time_limit

    def update(self, delta_time):
        self.update_oil_points(delta_time)

        for points in self.world:
            for point in points:
                point.pour_from_buffer()

        self.spread_oil_points(delta_time)

        for points in self.world:
            for point in points:
                point.pour_from_buffer()

        global total_time
        total_time += delta_time

    def update_oil_points(self, delta_time):
        for points in self.world:
            for point in points:
                if point.contain_oil():
                    point.update(delta_time)

    def generate_spreading_pairs(self):
        return (
                [((x, y), (x + 1, y)) for x in range(0, WORLD_SIDE_SIZE - 1, 2) for y in range(WORLD_SIDE_SIZE)]
                + [((x, y), (x + 1, y)) for x in range(1, WORLD_SIDE_SIZE - 1, 2) for y in range(WORLD_SIDE_SIZE)]
                + [((x, y), (x, y + 1)) for y in range(0, WORLD_SIDE_SIZE - 1, 2) for x in range(WORLD_SIDE_SIZE)]
                + [((x, y), (x, y + 1)) for y in range(1, WORLD_SIDE_SIZE - 1, 2) for x in range(WORLD_SIDE_SIZE)]
        )

    def spread_oil_points(self, delta_time: float):
        for pair in self.spreading_pairs:
            first, second = pair
            self.process_spread_between(delta_time, self.from_coords(first), self.from_coords(second))

    def process_spread_between(self, delta_time: float, first: Point, second: Point) -> None:
        if not (first.contain_oil() or second.contain_oil()) or not (
                first.topography == TopographyState.SEA and second.topography == TopographyState.SEA):
            return

        length = POINT_SIDE_SIZE
        V = self.current_oil_volume
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
        to_cell.emulsification_rate = (to_cell.emulsification_rate * to_cell.oil_mass + from_cell.emulsification_rate * real_delta) / (
                to_cell.oil_mass + real_delta)
        to_cell.oil_mass += real_delta

    def from_coords(self, coord) -> Point:
        x, y = coord
        return self.world[x][y]

    def load_topography(self):
        path = 'data/topography.csv'
        if os.getcwd().endswith('src'):
            path = '../' + path
        with open(path, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            for y, row in enumerate(reader):
                for x, state in enumerate(row):
                    if state == '1':
                        self.world[x][y].topography = TopographyState.LAND
