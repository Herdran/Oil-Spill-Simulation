from enum import Enum
from math import exp, log, sqrt
from random import randrange
from re import S
import numpy as np

from constatnts import WORLD_SIDE_SIZE, CELL_SIDE_SIZE, POINT_SIDE_SIZE


class TopographyState(Enum):
    LAND = 0
    SEA = 1


class InitialValues:
    def __init__(self):
        self.density = 835  # [kg/m^3]
        self.viscosity = 40  # tbh chuj wi
        self.surface_tension = 30  # [dyne/s]
        self.time_limit = 200  # [h]
        self.emulsion_max_content_water = 0.7  # max content of water in the emulsion
        self.molar_mass = 348.23  # [g/mol] mean
        self.boiling_point = 609  # [K] mean
        self.interfacial_tension = 28 # [dyna/cm] # TODO not sure :v probably not correct
        self.propagation_factor = 2.5
        self.c = 1  # nie wiem co to jest ale oczekuje tego na 71 więc dodałem 1 jako placeholder

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.wind_velocity = np.array([-0.1, -0.6])  # TODO vector
        self.wave_velocity = np.array([1.1, 0.2])  # TODO vector
        self.temperature = 298  # [K]


class Point:
    world = []

    def __init__(self, x, y, initial_values: InitialValues, cell: Cell):
        self.topography = TopographyState.SEA
        self.x = x
        self.y = y
        self.cell = cell
        self.oil_mass = 0  # [kg]
        self.initial_values = initial_values
        self.emulsification_rate = 0  # tbh chuj wi
        self.viscosity = initial_values.viscosity  # [cP]
        self.oil_buffer = 0  # contains oil which was added in current step
        self.evaporation_rate = 0

    def contain_oil(self) -> bool:
        return self.oil_mass > 0

    def update(self, delta_time: float) -> None:
        self.process_emulsification(delta_time)
        if self.topography == TopographyState.LAND:
            self.process_seashore_ineraction(delta_time)
        # TODO other processes
        delta_f = self.process_evaporation(delta_time)
        self.process_natural_dispersion(delta_time)
        self.viscosity_change(delta_f, 0.01) # #TODO water content?? 

        # to na końcu na pewno
        self.process_advection(delta_time)
        self.pour_from_buffer()

    def process_emulsification(self, delta_time: float) -> None:
        K = 2.0e-6

        self.emulsification_rate += delta_time * K * (
                ((self.cell.wind_velocity + 1) ** 2) * (
                1 - self.emulsification_rate / self.initial_values.c))

    def process_evaporation(self, delta_time: float) -> None:
        K = 1.25e-3
        P = 1000 * exp(-(4.4 + log(self.initial_values.boiling_point)) * (
                1.803 * (self.initial_values.boiling_point / self.cell.temperature - 1) - 0.803 * log(
            self.initial_values.boiling_point / self.cell.temperature)))  # [Pa]
        R = 8.314  # [J/(mol*K)]

        self.evaporation_rate = (K * (self.initial_values.molar_mass / 1000) * P) / (R * self.cell.temperature)
        delta_f = -1 * delta_time * POINT_SIDE_SIZE * POINT_SIDE_SIZE * self.evaporation_rate  # TODO check if sign is correct
        self.oil_mass += delta_f
        return delta_f

    def process_seashore_ineraction(self, delta_time: float) -> None:
        delta_mass = -log(2) * self.oil_mass * delta_time / (3600 * 24)
        # TODO iterate over neighbors and add oil if it is the sea

    def process_advection(self, delta_time: float) -> None:
        alpha = 1.1
        beta = 0.03
        delta_r = (alpha * self.cell.wave_velocity + beta * self.cell.wind_velocity) * delta_time
        # TODO teraz założenie że jedna kratka to jeden metr, żeby działo trzeba niżej pomnożyć
        if 0 <= self.x+int(delta_r[0]) < WORLD_SIDE_SIZE and 0 <= self.y+int(delta_r[1]) < WORLD_SIDE_SIZE:
            self.world[self.x+int(delta_r[0])][self.y+int(delta_r[1])].oil_buffer += self.oil_mass
        self.oil_mass = 0

    def process_natural_dispersion(self, delta_time: float) -> None:
        Da = 0.11 * (sqrt(self.cell.wind_velocity[0]**2+self.cell.wind_velocity[1]**2) + 1) ** 2
        interfacial_tension = self.initial_values.interfacial_tension * (1 + self.evaporation_rate) 
        Db = 1 / (1 + 50 * sqrt(self.viscosity) * self.slick_thickness() * interfacial_tension)
        self.oil_mass -= self.oil_mass * Da * Db / (3600 * delta_time)  # TODO check if sign is correct

    def slick_thickness(self) -> float:
        thickness = (self.oil_mass / self.initial_values.density) / (POINT_SIDE_SIZE ** 2)  # [m]
        return thickness / 100  # [cm]

    def viscosity_change(self, delta_F: float, delta_Y: float) -> None:
        C2 = 10
        delta_viscosity = (C2 * self.viscosity * delta_F + 2.5 * self.viscosity * delta_Y) / (
                    (1 - self.initial_values.emulsion_max_content_water * delta_Y) ** 2)
        self.viscosity += delta_viscosity  # TODO check if sign is correct

    def pour_from_buffer(self):
        self.oil_mass += self.oil_buffer
        self.oil_buffer = 0

class SimulationEngine:
    def __init__(self):
        self.total_time = 0
        self.initial_values = InitialValues()
        self.cells = [[Cell(x, y) for y in range(WORLD_SIDE_SIZE)]
                      for x in range(WORLD_SIDE_SIZE)]
        self.world = [[Point(x, y, self.initial_values, self.cells[x // CELL_SIDE_SIZE][y // CELL_SIDE_SIZE])
                       for y in range(WORLD_SIDE_SIZE)]
                      for x in range(WORLD_SIDE_SIZE)]
        Point.world = self.world
        self.spreading_pairs = self.generate_spreading_pairs()
        self.current_oil_volume = 0 # TODO 

    def start(self, preset_path):
        # TODO load Topography - currently I have no idea how xD
        # TODO deserialize initial_values from json (preset_path)
        for points in self.world:
            for point in points:
                point.oil_mass = randrange(0, 2)
        # self.world[0][0].oil_mass = 2
        # self.world[0][1].oil_mass = 2
        # self.world[0][2].oil_mass = 2
        # self.world[0][3].oil_mass = 2
        # self.world[0][4].oil_mass = 2
        # self.world[0][5].oil_mass = 2
        # self.world[1][0].oil_mass = 2
        # self.world[2][0].oil_mass = 2
        # self.world[3][0].oil_mass = 2
        # self.world[4][0].oil_mass = 2
        # self.world[5][0].oil_mass = 2
        # pass

    def is_finished(self):
        return self.total_time >= self.initial_values.time_limit

    def update(self, delta_time):
        self.update_oil_points(delta_time)
        self.spread_oil_points(delta_time)

        self.total_time += delta_time

    def update_oil_points(self, delta_time):
        for points in self.world:
            for point in points:
                if (point.contain_oil):
                    point.update(delta_time)

    def generate_spreading_pairs(self):
        rows = [((x, y), (x+1, y)) for x in range(WORLD_SIDE_SIZE - 1) for y in range(WORLD_SIDE_SIZE)]
        cols = [((x, y), (x, y+1)) for y in range(WORLD_SIDE_SIZE - 1) for x in range(WORLD_SIDE_SIZE)]
        return rows + cols

    def spread_oil_points(self, delta_time: float):
        for pair in self.spreading_pairs:
            first, second = pair
            self.process_spread_between(delta_time, self.from_coords(first), self.from_coords(second))
    
    def process_spread_between(self, delta_time: float, first: Point, second: Point) -> None:  
        length = 1 # TODO dunno xD
        V = self.current_oil_volume
        g = 9.8 
        delta = 1 # TODO
        viscosity = 0.5 * (first.viscosity + second.viscosity)
        D = 0.48 / self.initial_values.propagation_factor * (V**2 * g * delta / sqrt(viscosity)) ** (1/3) / sqrt(delta_time) 
        delta_mass = 0.5 * (first.oil_mass - second.oil_mass) * (1 - exp(-2 * D/(length**2) * delta_time))
        #TODO dunno czy to powinno byc tu czy nie
        first.oil_mass -= delta_mass
        second.oil_mass += delta_mass

    def from_coords(self, coord) -> Point:
        x, y = coord
        return self.world[x][y]  