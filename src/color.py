from initial_values import InitialValues
from simulation.point import TopographyState, Point

COLOR_RANGE_MAX = 255.0


def blend_color(color1, color2, ratio) -> tuple[int, ...]:
    ratio = min(ratio, 1)
    return tuple(int(color1[i] * ratio + color2[i] * (1 - ratio)) for i in range(len(color1)))


def changed_color(minimal_oil_to_show: float, point: Point):
    if point.topography == TopographyState.LAND:
        var = blend_color(InitialValues.LAND_WITH_OIL_COLOR, InitialValues.LAND_COLOR,
                          point.oil_mass / minimal_oil_to_show)
    else:
        var = blend_color(InitialValues.OIL_COLOR, InitialValues.SEA_COLOR,
                          point.oil_mass / minimal_oil_to_show)
    if point.pixel_color != var:
        point.pixel_color = var
        return True
    return False
