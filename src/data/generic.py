from dataclasses import dataclass
from typing import Generic, TypeVar


GenericT = TypeVar("GenericT")

@dataclass
class Range(Generic[GenericT]):
    min: GenericT
    max: GenericT