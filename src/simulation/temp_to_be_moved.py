from color import blend_color
from initial_values import InitialValues
from simulation.point import TopographyState, Point


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
# TODO functionality of this method should be performed after last update process for each point, so that it
#  won't have to be run after all the updates are done and on all at the same time