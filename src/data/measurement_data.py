import math
from dataclasses import dataclass
from typing import Generic, Optional

import numpy as np

from data.generic import GenericT


@dataclass
class CoordinatesBase(Generic[GenericT]):
    latitude: GenericT
    longitude: GenericT

    def as_tuple(self) -> tuple[GenericT, GenericT]:
        return self.latitude, self.longitude


Coordinates = CoordinatesBase[float]
'''
latitude range: -90.0 to 90.0
longitude range: -180.0 to 180.0
'''

Temperature = float
'''
Value of temperature in kelvins
'''


def average_measurement(measurements: list[float], weights: float) -> list[float]:
    return np.average(measurements, weights=weights)


@dataclass
class SpeedMeasure:
    speed_north: float  # m/s
    speed_east: float  # m/s

    @staticmethod
    def from_direction(speed: float, direction: float) -> 'SpeedMeasure':
        return SpeedMeasure(
            speed_north=speed * math.cos(math.radians(direction)),
            speed_east=speed * math.sin(math.radians(direction))
        )

    @staticmethod
    def from_average(measurements: 'SpeedMeasure', weights: float) -> 'SpeedMeasure':
        return SpeedMeasure(
            speed_north=average_measurement([measurement.speed_north for measurement in measurements], weights),
            speed_east=average_measurement([measurement.speed_east for measurement in measurements], weights)
        )

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.speed_north
        elif index == 1:
            return self.speed_east
        else:
            raise IndexError(f'Index {index} out of range')

    @staticmethod
    def from_numpy(np_array):
        return SpeedMeasure(np_array[0], np_array[1])

    def to_numpy(self):
        return np.array([self.speed_north, self.speed_east])


@dataclass
class Measurement:
    wind: Optional[SpeedMeasure]
    current: Optional[SpeedMeasure]
    temperature: Optional[Temperature]


@dataclass
class CertainMeasurement:
    wind: SpeedMeasure
    current: SpeedMeasure
    temperature: Temperature
