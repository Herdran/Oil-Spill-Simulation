from typing import Tuple
from enum import Enum

import numpy as np
import pandas as pd
from numpy import exp, log, sqrt

from constatnts import InitialValues
from data.measurment_data import Coordinates
from simulation.utilities import get_neighbour_coordinates, Neighbourhood, sign

DEFAULT_WAVE_VELOCITY = np.array([0.0, 0.0])  # [m/s]
DEFAULT_WIND_VELOCITY = np.array([0.0, 0.0])  # [m/s]
DEFAULT_TEMPERATURE = 302.15  # [K]

Coord_t = Tuple[int, int]


class TopographyState(Enum):
    LAND = 0
    SEA = 1


class Point:
    world = dict()

    def __init__(self, coord: Coord_t, engine):
        self.topography = engine.get_topography(coord)
        self.engine = engine
        self.coord = coord
        x, y = coord
        self.coordinates = Coordinates(latitude=InitialValues.point_lat_centers[y], longitude=InitialValues.point_lon_centers[x])
        self.weather_station_coordinates = engine.data_processor.weather_station_coordinates(self.coordinates)
        self.wind_velocity = DEFAULT_WIND_VELOCITY
        self.wave_velocity = DEFAULT_WAVE_VELOCITY
        self.temperature = DEFAULT_TEMPERATURE
        self.last_weather_update_time = None
        self.oil_mass = 0  # [kg]
        self.emulsification_rate = InitialValues.emulsification_rate
        self.data_processor = engine.data_processor
        self.viscosity_dynamic = InitialValues.viscosity_dynamic  # [Pa*s]
        self.oil_buffer = []  # contains tuples (mass, viscosity, emulsification_rate)
        self.evaporation_rate = 0

    def contain_oil(self) -> bool:
        # TODO dynamic value based on point area
        return self.oil_mass > 1

    def add_oil(self, mass: float) -> None:
        # maybe initial emulsification rate will be changed
        self.emulsification_rate = (self.oil_mass * self.emulsification_rate +
                                    mass * InitialValues.emulsification_rate) / (self.oil_mass + mass)
        self.viscosity_dynamic = (
                (self.oil_mass * self.viscosity_dynamic + mass * InitialValues.viscosity_dynamic) / (
                self.oil_mass + mass))
        self.oil_mass += mass

    def should_update_weather_data(self, time_delta: pd.Timedelta) -> bool:
        return (self.last_weather_update_time is None
                or self.data_processor.should_update_data(time_delta - self.last_weather_update_time))

    def update_weather_data(self) -> None:
        time_delta = pd.Timedelta(seconds=int(self.engine.total_time))
        if self.should_update_weather_data(time_delta):
            time_stamp = InitialValues.simulation_initial_parameters.time.min + time_delta
            measurment = self.data_processor.get_measurment(self.coordinates, self.weather_station_coordinates,
                                                            time_stamp)
            self.wave_velocity = measurment.current.to_numpy()
            self.wind_velocity = measurment.wind.to_numpy()
            self.temperature = measurment.temperature
            self.last_weather_update_time = time_delta

    def update(self) -> None:
        self.update_weather_data()
        if self.topography == TopographyState.LAND:
            self.process_seashore_interaction()
            return
        delta_y = self.process_emulsification()
        delta_f = self.process_evaporation()
        self.process_natural_dispersion()
        self.viscosity_change(delta_f, delta_y)

        # to na końcu na pewno
        self.process_advection()

    def process_emulsification(self) -> float:
        K = 5.0e-7
        old_emulsification_rate = self.emulsification_rate
        self.emulsification_rate += InitialValues.iter_as_sec * K * (
                ((np.linalg.norm(self.wind_velocity) + 1) ** 2) * (
                1 - self.emulsification_rate / InitialValues.emulsion_max_content_water))
        if self.emulsification_rate > InitialValues.emulsion_max_content_water:
            self.emulsification_rate = InitialValues.emulsion_max_content_water
        return self.emulsification_rate - old_emulsification_rate

    def process_evaporation(self) -> float:
        K = 1.25e-3
        P = 1000 * exp(-(4.4 + log(InitialValues.boiling_point)) * (
                1.803 * (InitialValues.boiling_point / self.temperature - 1) - 0.803 * log(
            InitialValues.boiling_point / self.temperature)))  # [Pa]
        R = 8.314  # [J/(mol*K)]

        self.evaporation_rate = (K * (InitialValues.molar_mass / 1000) * P) / (R * self.temperature)
        delta_mass = -1 * min(InitialValues.iter_as_sec * InitialValues.point_side_size * InitialValues.point_side_size * self.evaporation_rate,
                              self.oil_mass)
        delta_f = -delta_mass / self.oil_mass
        self.oil_mass += delta_mass
        return delta_f

    def process_seashore_interaction(self) -> None:
        half_time = 3600 * 24  # 24h for sand beach / sand and gravel beach
        delta_mass = log(2) * self.oil_mass * InitialValues.iter_as_sec / half_time
        self.oil_mass -= delta_mass
        to_share = []
        (x, y) = self.coord

        neighbours = get_neighbour_coordinates(x, y, InitialValues.neighbourhood)
        for cords in neighbours:
            if not ((0 <= cords[0] < InitialValues.point_side_count) and (0 <= cords[1] < InitialValues.point_side_count)):
                continue
            if cords in self.engine.lands:
                continue
            if cords not in self.world:
                self.world[cords] = Point(cords, self.engine)
                self.engine.points_changed.append(cords)
            to_share.append(self.world[cords])
        if len(to_share) == 0:  # in case of bug
            return
        delta_mass /= len(to_share)
        for neighbor in to_share:
            neighbor.oil_mass += delta_mass

    def advection_land_collision(self, advection_vector: Tuple[float, float]) -> Tuple[int, int, Tuple[float, float]]:
        x, y = self.coord
        next_x = x + int(advection_vector[0])
        next_y = y + int(advection_vector[1])
        for i in range(1, int(max(map(abs, advection_vector)))):
            advection_x, advection_y = advection_vector
            if abs(advection_x) > abs(advection_y):
                crossing_point = (x + i * sign(advection_x), y + round(i * advection_y / abs(advection_x)))
            else:
                crossing_point = (round(x + i * advection_x / abs(advection_y)), y + i * sign(advection_y))
            if self.engine.get_topography(crossing_point) == TopographyState.LAND:
                next_x, next_y = map(int, crossing_point)
                advection_vector = (0, 0)  # so it's not going through land in the next step
                break
        return next_x, next_y, advection_vector

    def process_advection(self) -> None:
        ALPHA = 1.1
        BETA = 0.03

        delta_r = (ALPHA * self.wave_velocity + BETA * self.wind_velocity) * InitialValues.iter_as_sec
        delta_r /= InitialValues.point_side_size
        advection_vector = (delta_r[1], -delta_r[0])

        # check if there is a land between current and next point
        next_x, next_y, advection_vector = self.advection_land_collision(advection_vector)

        fractional_part_x = (abs(advection_vector[0]) % 1) * sign(advection_vector[0])
        fractional_part_y = (abs(advection_vector[1]) % 1) * sign(advection_vector[1])
        x_shift = sign(fractional_part_x)
        y_shift = sign(fractional_part_y)
        neighbours = [(next_x, next_y + y_shift), (next_x + x_shift, next_y), (next_x + x_shift, next_y + y_shift)]
        areas = [abs(fractional_part_y) * (1 - abs(fractional_part_x)),
                 abs(fractional_part_x) * (1 - abs(fractional_part_y)),
                 abs(fractional_part_x * fractional_part_y)]
        if InitialValues.neighbourhood == Neighbourhood.VON_NEUMANN:
            neighbours.pop()
            area_to_split = areas.pop()
            if sum(areas) > 0:
                areas[0] += area_to_split * areas[0] / sum(areas)
                areas[1] += area_to_split * areas[1] / sum(areas)
        oil_mass = self.oil_mass
        for neighbour, area in zip(neighbours, areas):
            self.move_oil_to_other(neighbour, oil_mass * area)

        if (next_x, next_y) != self.coord:
            self.move_oil_to_other((next_x, next_y), self.oil_mass)

    def process_natural_dispersion(self) -> None:
        Da = 0.11 * (np.linalg.norm(self.wind_velocity) + 1) ** 2
        interfacial_tension = InitialValues.interfacial_tension * (1 + self.evaporation_rate)
        # multiply viscosity by 100 to convert from Pa*s to cPa*s
        Db = 1 / (1 + 50 * sqrt(self.viscosity_dynamic * 100) * self.slick_thickness() * interfacial_tension)
        self.oil_mass -= self.oil_mass * Da * Db / (3600 * InitialValues.iter_as_sec)

    def slick_thickness(self) -> float:
        thickness = (self.oil_mass / InitialValues.oil_density) / (InitialValues.point_side_size ** 2)  # [m]
        return thickness * 100  # [cm]

    def viscosity_change(self, delta_F: float, delta_Y: float) -> None:
        delta_viscosity = InitialValues.c * self.viscosity_dynamic * delta_F + (
                2.5 * self.viscosity_dynamic * delta_Y) / (
                                  (1 - InitialValues.emulsion_max_content_water * self.emulsification_rate) ** 2)
        self.viscosity_dynamic += delta_viscosity
        if self.oil_mass < 1:
            self.viscosity_dynamic = InitialValues.viscosity_dynamic

    def pour_from_buffer(self):
        oil_mass = sum([tup[0] for tup in self.oil_buffer]) + self.oil_mass
        if oil_mass < 1:
            return
        self.viscosity_dynamic = (sum([tup[0] * tup[1] for tup in
                                       self.oil_buffer]) + self.oil_mass * self.viscosity_dynamic) / oil_mass
        self.emulsification_rate = (sum([tup[0] * tup[2] for tup in
                                         self.oil_buffer]) + self.oil_mass * self.emulsification_rate) / oil_mass
        self.oil_buffer = []
        self.oil_mass = oil_mass

    def move_oil_to_other(self, coord: Coord_t, mass: float) -> None:
        self.oil_mass -= mass
        if not (0 <= coord[0] < InitialValues.point_side_count and 0 <= coord[1] < InitialValues.point_side_count):
            return
        if coord not in self.world:
            self.world[coord] = Point(coord, self.engine)
            self.engine.points_changed.append(coord)
        self.world[coord].oil_buffer.append((mass, self.viscosity_dynamic, self.emulsification_rate))
