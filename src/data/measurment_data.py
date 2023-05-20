from dataclasses import dataclass
from typing import Optional


@dataclass
class Coordinates:
    '''
    latitude range: -90.0 to 90.0
    longitude range: -180.0 to 180.0
    '''

    latitude: float
    longitude: float


@dataclass
class SpeedMeasure:
    speed: float      # m/s
    direction: float  # degrees


@dataclass
class Measurment:
    wind: Optional[SpeedMeasure]
    current: Optional[SpeedMeasure]


@dataclass
class CertainMeasurment:
    wind: SpeedMeasure
    current: SpeedMeasure
