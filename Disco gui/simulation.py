from enum import Enum
from math import exp, log, sqrt

from constatnts import WORLD_SIDE_SIZE, CELL_SIDE_SIZE, POINT_SIDE_SIZE


class TopographyState(Enum):
    LAND = 0
    SEA = 1


class InitialValues:
    def __init__(self):
        self.density = 835  # [kg/m^3]
        self.viscosity = 0  # tbh chuj wi
        self.surface_tension = 30  # [dyne/s]
        self.composition = 0  # TODO calculate mean from values in paper
        self.time_limit = 200  # [h]
        self.emulsion_max_content_water = 0.7  # max content of water in the emulsion
        self.molar_mass = 348.23  # [g/mol] mean
        self.boiling_point = 609  # [K] mean
        self.interfacial_tension = 28 # [dyna/cm] # TODO not sure :v probably not correct


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.wind_velocity = 0  # TODO vector
        self.wave_velocity = 0  # TODO vector
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
        self.viscosity = 0  # [cP]
        self.oil_buffer = 0  # contains oil which was added in current step

    def contain_oil(self) -> bool:
        return self.oil_mass > 0

    def update(self, delta_time: float) -> None:
        self.process_emulsification(delta_time)
        if self.topography == TopographyState.LAND:
            self.process_seashore_ineraction(delta_time)
        # TODO other processes
        self.process_evaporation(delta_time)
        self.process_natural_dispersion(delta_time)

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

        evaporation_rate = (K * (self.initial_values.molar_mass / 1000) * P) / (R * self.cell.temperature)
        self.oil_mass -= delta_time * POINT_SIDE_SIZE * POINT_SIDE_SIZE * evaporation_rate  # TODO check if sign is correct

    def process_seashore_ineraction(self, delta_time: float) -> None:
        delta_mass = -log(2) * self.oil_mass * delta_time / (3600 * 24)
        # TODO iterate over neighbors and add oil if it is the sea

    def process_advection(self, delta_time: float) -> None:
        alpha = 1.1
        beta = 0.03
        delta_r = (alpha * self.cell.wave_velocity + beta * self.cell.wind_velocity) * delta_time
        # TODO zrobić z wektora wartości całkowite
        self.world[self.x+delta_r[0]][self.y+delta_r[1]].oil_buffer += self.oil_mass
        self.oil_mass = 0

    def process_natural_dispersion(self, delta_time: float, evaporation_rate: float) -> None: #TODO evaporation rate - tam na koncu dokumentu jest to opisane ale nw :v
        Da = 0.11 * (self.cell.wind_velocity + 1) ** 2
        interfacial_tension = self.initial_values.interfacial_tension * (1 + evaporation_rate) 
        Db = 1 / (1 + 50 * sqrt(self.viscosity) * self.slick_thickness() * interfacial_tension)
        self.oil_mass -= self.oil_mass * Da * Db / (3600 * delta_time)  # TODO check if sign is correct

    def slick_thickness(self) -> float:
        thickness = (self.oil_mass / self.initial_values.density) / (POINT_SIDE_SIZE ** 2)  # [m]
        return thickness / 100  # [cm]

    def viscosity_change(self, delta_F: float, delta_Y: float) -> None:
        C2 = 10
        delta_viscosity = (C2 * self.viscosity * delta_F + 2.5 * self.viscosity * delta_Y) / (
                    (1 - self.initial_values.emulsion_max_content_water * delta_Y) ** 2)
        # TODO

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

    def start(self, preset_path):
        # TODO load Topography - currently I have no idea how xD
        # TODO deserialize initial_values from json (preset_path)
        pass

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

    def spread_oil_points(self, delta_time):
        pass  # TODO
