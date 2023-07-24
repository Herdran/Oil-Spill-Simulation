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

@dataclass
class SpeedMeasure():
    speed_north: float  # m/s
    speed_east: float   # m/s
    
    @staticmethod
    def from_direction(speed: float, direction: float) -> 'SpeedMeasure':
        speed_north = speed * math.cos(math.radians(direction))
        speed_east = speed * math.sin(math.radians(direction))
        return SpeedMeasure(speed_north, speed_east)
    
    @staticmethod
    def try_from_repr(repr: str) -> Optional['SpeedMeasure']:
        re_result = re.match(r"SpeedMeasure\((.*),(.*)\)", repr)
        if re_result is None or len(re_result.groups()) != 2:
            return None
        speed_north = float(re_result.group(1))
        speed_east = float(re_result.group(2))
        return SpeedMeasure(speed_north, speed_east)
    
    def to_numpy(self):
        return np.array([self.speed_north, self.speed_east])
        
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.speed_north},{self.speed_east})"


@dataclass
class Measurment:
    wind: Optional[SpeedMeasure]
    current: Optional[SpeedMeasure]


@dataclass
class CertainMeasurment:
    wind: SpeedMeasure
    current: SpeedMeasure
