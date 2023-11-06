from enum import Enum
from typing import Tuple, List


class Neighbourhood(Enum):
    VON_NEUMANN = 0
    MOORE = 1


def get_neighbour_coordinates(x: int, y: int, neighbourhood: Neighbourhood) -> List[Tuple[int, int]]:
    if neighbourhood == Neighbourhood.VON_NEUMANN:
        return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    elif neighbourhood == Neighbourhood.MOORE:
        return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
                (x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)]
    else:
        raise ValueError("Unknown neighbourhood type")
