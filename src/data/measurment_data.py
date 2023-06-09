from dataclasses import dataclass
import math
from typing import Generic, Optional
from generic import GenericT

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
class SpeedMeasure:
    speed_north: float  # m/s
    speed_east: float   # m/s
    
    @staticmethod
    def from_direction(speed: float, direction: float) -> 'SpeedMeasure':
        speed_north = speed * math.cos(math.radians(direction))
        speed_east = speed * math.sin(math.radians(direction))
        return SpeedMeasure(speed_north, speed_east)
        


@dataclass
class Measurment:
    wind: Optional[SpeedMeasure]
    current: Optional[SpeedMeasure]


@dataclass
class CertainMeasurment:
    wind: SpeedMeasure
    current: SpeedMeasure
