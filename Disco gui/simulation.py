from enum import Enum

from constatnts import WORD_SIDE_SIZE, CELL_SIDE_SIZE


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
        self.c = 0.7  # max content of water in the emulsion


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.wind_velocity = 0  # TODO


class Point:
    def __init__(self, x, y, initial_values: InitialValues, cell: Cell):
        self.topography = TopographyState.SEA
        self.x = x
        self.y = y
        self.cell = cell
        self.initial_values = initial_values
        self.emulsification_rate = 0  # tbh chuj wi

    def contain_oil(self):
        return True  # TODO

    def update(self, delta_time):
        self.process_emulsification(delta_time)
        # TODO other processes

    def process_emulsification(self, delta_time):
        K = 2.0e-6

        self.emulsification_rate += delta_time * K * (
            ((self.cell.wind_velocity + 1) ** 2) * (
                1 - self.emulsification_rate / self.initial_values.c))


class SimulationEngine:
    def __init__(self):
        self.total_time = 0
        self.initial_values = InitialValues()
        self.cells = [[Cell(x, y) for y in range(WORD_SIDE_SIZE)]
                      for x in range(WORD_SIDE_SIZE)]
        self.word = [[Point(x, y, self.initial_values, self.cells[x // CELL_SIDE_SIZE][y // CELL_SIDE_SIZE])
                      for y in range(WORD_SIDE_SIZE)]
                     for x in range(WORD_SIDE_SIZE)]

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
        for points in self.word:
            for point in points:
                if (point.contain_oil):
                    point.update(delta_time)

    def spread_oil_points(self, delta_time):
        pass  # TODO
