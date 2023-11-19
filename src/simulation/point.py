from typing import Tuple
from enum import Enum

import numpy as np
import pandas as pd
from numpy import exp, log, sqrt

import constatnts as const
from data.measurment_data import Coordinates
from simulation.utilities import get_neighbour_coordinates, Neighbourhood

DEFAULT_WAVE_VELOCITY = np.array([0.0, 0.0])  # [m/s]
DEFAULT_WIND_VELOCITY = np.array([0.0, 0.0])  # [m/s]
DEFAULT_TEMPERATUTRE = 302.15  # [K]

Coord_t = Tuple[int, int]


class TopographyState(Enum):
    LAND = 0
    SEA = 1


class InitialValues:
    def __init__(self, neighbourhood: Neighbourhood = Neighbourhood.MOORE):
        self.water_density = 997  # [kg/m^3]
        self.density = 835  # [kg/m^3]
        self.surface_tension = 30  # [dyne/s]
        self.emulsion_max_content_water = 0.7  # max content of water in the emulsion
        self.molar_mass = 348.23  # [g/mol] mean
        self.boiling_point = 609  # [K] mean
        self.interfacial_tension = 30  # [dyna/cm]
        self.propagation_factor = 2.5
        self.c = 0.7  # constant from paper
        self.viscosity = 10  # TODO: what is that value?
        self.emulsification_rate = 0.01
        self.neighbourhood = neighbourhood


class Point:
    world = dict()

    def __init__(self, coord: Coord_t, initial_values: InitialValues, engine):
        self.topography = engine.get_topography(coord)
        self.engine = engine
        self.coord = coord
        x, y = coord
        self.coordinates = Coordinates(latitude=const.POINT_LAT_CENTERS[y], longitude=const.POINT_LON_CENTERS[x])
        self.weather_station_coordinates = engine.data_processor.weather_station_coordinates(self.coordinates)
        self.wind_velocity = DEFAULT_WIND_VELOCITY
        self.wave_velocity = DEFAULT_WAVE_VELOCITY
        self.temperature = DEFAULT_TEMPERATUTRE
        self.last_weather_update_time = None
        self.oil_mass = 0  # [kg]
        self.initial_values = initial_values
        self.emulsification_rate = initial_values.emulsification_rate
        self.data_processor = engine.data_processor
        self.viscosity = initial_values.viscosity  # [cP]
        self.oil_buffer = []  # contains tuples (mass, viscosity, emulsification_rate)
        self.advection_buffer = np.array([0, 0], dtype='float64')
        self.evaporation_rate = 0

    def contain_oil(self) -> bool:
        # TODO dynamic value based on point area
        return self.oil_mass > 1

    def add_oil(self, mass: float) -> None:
        # maybe initial emulsification rate will be changed
        self.emulsification_rate = (self.oil_mass * self.emulsification_rate +
                                    mass * self.initial_values.emulsification_rate) / (self.oil_mass + mass)
        self.viscosity = (self.oil_mass * self.viscosity + mass * self.initial_values.viscosity) / (
                self.oil_mass + mass)
        self.oil_mass += mass

    def should_update_weather_data(self, time_delta: pd.Timedelta) -> bool:
        return (self.last_weather_update_time is None
                or self.data_processor.should_update_data(time_delta - self.last_weather_update_time))

    def update_weather_data(self) -> None:
        time_delta = pd.Timedelta(seconds=int(self.engine.total_time))
        if self.should_update_weather_data(time_delta):
            time_stamp = const.SIMULATION_INITIAL_PARAMETERS.time.min + time_delta
            measurment = self.data_processor.get_measurment(self.coordinates, self.weather_station_coordinates,
                                                            time_stamp)
            self.wave_velocity = measurment.current.to_numpy()
            self.wind_velocity = measurment.wind.to_numpy()
            self.temperature = measurment.temperature
            self.last_weather_update_time = time_delta

    def update(self, delta_time: float) -> None:
        self.update_weather_data()
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
                ((np.linalg.norm(self.wind_velocity) + 1) ** 2) * (
                1 - self.emulsification_rate / self.initial_values.c))
        if self.emulsification_rate > self.initial_values.emulsion_max_content_water:
            self.emulsification_rate = self.initial_values.emulsion_max_content_water
        return self.emulsification_rate - old_emulsification_rate

    def process_evaporation(self, delta_time: float) -> float:
        K = 1.25e-3
        P = 1000 * exp(-(4.4 + log(self.initial_values.boiling_point)) * (
                1.803 * (self.initial_values.boiling_point / self.temperature - 1) - 0.803 * log(
            self.initial_values.boiling_point / self.temperature)))  # [Pa]
        R = 8.314  # [J/(mol*K)]

        self.evaporation_rate = (K * (self.initial_values.molar_mass / 1000) * P) / (R * self.temperature)
        delta_mass = -1 * min(delta_time * const.POINT_SIDE_SIZE * const.POINT_SIDE_SIZE * self.evaporation_rate,
                              self.oil_mass)
        delta_f = -delta_mass / self.oil_mass
        self.oil_mass += delta_mass
        return delta_f

    def process_seashore_interaction(self, delta_time: float) -> None:
        half_time = 3600 * 24  # 24h for sand beach / sand and gravel beach
        delta_mass = log(2) * self.oil_mass * delta_time / half_time
        self.oil_mass -= delta_mass
        to_share = []
        (x, y) = self.coord

        neighbours = get_neighbour_coordinates(x, y, self.initial_values.neighbourhood)
        for cords in neighbours:
            if not ((0 <= cords[0] < const.POINTS_SIDE_COUNT) and (0 <= cords[1] < const.POINTS_SIDE_COUNT)):
                continue
            if cords in self.engine.lands:
                continue
            if cords not in self.world:
                self.world[cords] = Point(cords, self.initial_values, self.engine)
                self.engine.points_changed.append(cords)
            to_share.append(self.world[cords])
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
        ALPHA = 1.1
        BETA = 0.03

        delta_r = (ALPHA * self.wave_velocity + BETA * self.wind_velocity) * delta_time
        delta_r /= const.POINT_SIDE_SIZE

        # buffering how far oil went in time step
        self.advection_buffer += [delta_r[1], -delta_r[0]]
        x, y = self.coord
        next_x = x + int(self.advection_buffer[0])
        next_y = y + int(self.advection_buffer[1])

        # check if there is a land between current and next point
        for i in range(1, int(max(map(abs, self.advection_buffer)))):
            advection_x, advection_y = self.advection_buffer
            if abs(advection_x) > abs(advection_y):
                # multiplying by advection_x / abs(advection_x) to get sign of advection_x
                crossing_point = (x + i * advection_x / abs(advection_x), y + round(i * advection_y / abs(advection_x)))
            else:
                # multiplying by advection_y / abs(advection_y) to get sign of advection_y
                crossing_point = (round(x + i * advection_x / abs(advection_y)), y + i * advection_y / abs(advection_y))
            if self.engine.get_topography(crossing_point) == TopographyState.LAND:
                next_x, next_y = map(int, crossing_point)
                # to ensure that buffer will be zeroed in a next step, because oil can't go further
                self.advection_buffer = np.array([next_x - x, next_y - y], dtype='float64')
                break

        if 0 <= next_x < const.POINTS_SIDE_COUNT and 0 <= next_y < const.POINTS_SIDE_COUNT:
            if (next_x, next_y) not in self.world:
                self.world[(next_x, next_y)] = Point((next_x, next_y), self.initial_values, self.engine)
                self.engine.points_changed.append((next_x, next_y))
            self.world[(next_x, next_y)].oil_buffer.append((self.oil_mass, self.viscosity, self.emulsification_rate))
        self.advection_buffer -= np.array([next_x - x, next_y - y])
        self.oil_mass = 0

    def process_natural_dispersion(self, delta_time: float) -> None:
        Da = 0.11 * (np.linalg.norm(self.wind_velocity) + 1) ** 2
        interfacial_tension = self.initial_values.interfacial_tension * (1 + self.evaporation_rate)
        Db = 1 / (1 + 50 * sqrt(self.viscosity) * self.slick_thickness() * interfacial_tension)
        self.oil_mass -= self.oil_mass * Da * Db / (3600 * delta_time)

    def slick_thickness(self) -> float:
        thickness = (self.oil_mass / self.initial_values.density) / (const.POINT_SIDE_SIZE ** 2)  # [m]
        return thickness / 100  # [cm]

    def viscosity_change(self, delta_F: float, delta_Y: float) -> None:
        C2 = 10
        delta_viscosity = C2 * self.viscosity * delta_F + (2.5 * self.viscosity * delta_Y) / (
                (1 - self.initial_values.emulsion_max_content_water * self.emulsification_rate) ** 2)
        self.viscosity += delta_viscosity
        if self.oil_mass < 1:
            self.viscosity = self.initial_values.viscosity

    def pour_from_buffer(self):
        oil_mass = sum([tup[0] for tup in self.oil_buffer]) + self.oil_mass
        if oil_mass < 1:
            return
        self.viscosity = (sum([tup[0] * tup[1] for tup in self.oil_buffer]) + self.oil_mass * self.viscosity) / oil_mass
        self.emulsification_rate = (sum([tup[0] * tup[2] for tup in self.oil_buffer]) + self.oil_mass * self.emulsification_rate) / oil_mass
        self.oil_buffer = []
        self.oil_mass = oil_mass
