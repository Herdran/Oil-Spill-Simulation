import math
import re
from dataclasses import dataclass
from typing import Generic, Optional
from data.generic import GenericT
import numpy as np

@dataclass
class CoordinatesBase(Generic[GenericT]):
    latitude: GenericT
    longitude: GenericT
            

Coordinates = CoordinatesBase[float]
'''
latitude range: -90.0 to 90.0
longitude range: -180.0 to 180.0
'''

Temperature = float
'''
Value of temperature in kelvins
'''

def avrage_measurment(measurments: list[float], weights: float) -> list[float]:
    return np.average(measurments, weights=weights)

@dataclass
class SpeedMeasure():
    speed_north: float  # m/s
    speed_east: float   # m/s
    
    @staticmethod
    def from_direction(speed: float, direction: float) -> 'SpeedMeasure':
        return SpeedMeasure(
            speed_north = speed * math.cos(math.radians(direction)), 
            speed_east = speed * math.sin(math.radians(direction))
        )
    
    @staticmethod
    def from_average(measurments: 'SpeedMeasure', weights: float) -> 'SpeedMeasure':
        return SpeedMeasure(
            speed_north = avrage_measurment([measurment.speed_north for measurment in measurments], weights),
            speed_east = avrage_measurment([measurment.speed_east for measurment in measurments], weights)
        )
    
    @staticmethod
    def try_from_repr(repr: str) -> Optional['SpeedMeasure']:
        NORTH_SPEED_IDX = 1
        EAST_SPEED_IDX = 2
        GROUPS_COUNTS = 2
        
        re_result = re.match(r"SpeedMeasure\((.*),(.*)\)", repr)
        if re_result is None or len(re_result.groups()) != GROUPS_COUNTS:
            return None
        return SpeedMeasure(
            speed_north = float(re_result.group(NORTH_SPEED_IDX)),
            speed_east = float(re_result.group(EAST_SPEED_IDX))
        )
    
    @staticmethod
    def from_numpy(np_array):
        return SpeedMeasure(np_array[0], np_array[1])
    
    def to_numpy(self):
        return np.array([self.speed_north, self.speed_east])
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.speed_north},{self.speed_east})"


@dataclass
class Measurment:
    wind: Optional[SpeedMeasure]
    current: Optional[SpeedMeasure]
    temperature: Optional[Temperature]


@dataclass
class CertainMeasurment:
    wind: SpeedMeasure
    current: SpeedMeasure
    temperature: Temperature
