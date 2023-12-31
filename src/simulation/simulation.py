from typing import Any

import pandas as pd
from PIL.Image import Image

from checkpoints import save_to_json
from data.data_processor import DataProcessor
from initial_values import InitialValues
from simulation.temp_to_be_moved import changed_color
from simulation.point import Point, Coord_t, TopographyState
from simulation.spreading import SpreadingEngine
from topology.lands_loader import load_topography
from topology.math import get_xy_from_coord_raw


class SimulationEngine:
    def __init__(self, data_processor: DataProcessor):
        self._world: dict[Coord_t, Point] = dict()
        self.spreading_engine = SpreadingEngine(self)

        Point.world = self._world
        self.data_processor = data_processor
        self.checkpoint_frequency = InitialValues.checkpoint_frequency
        self.timestep = InitialValues.iter_as_sec
        self._total_mass = InitialValues.global_oil_amount_sea
        self._total_land_mass = InitialValues.global_oil_amount_land
        self.lands, self.x_indices, self.y_indices = load_topography()
        self._total_time = InitialValues.total_simulation_time
        self._constant_sources = []  # contains tuples (coord, mass_per_minute, spill_start, spill_end)
        self._evaporated_oil = InitialValues.evaporated_oil  # [kg]
        self._dispersed_oil = InitialValues.dispersed_oil  # [kg]
        self._simulation_image = None
        self.points_changed = set()
        self.points_removed = set()

    def is_finished(self) -> bool:
        return self._total_time >= InitialValues.simulation_time

    def update(self, minimal_oil_to_show):
        self.points_changed = set()
        self.points_removed = set()
        self._pour_from_sources()
        self._update_oil_points()

        self._total_mass = 0
        self._total_land_mass = 0
        for point in self._world.values():
            point.pour_from_buffer()
            self._total_mass += point.oil_mass
            if point.topography == TopographyState.LAND:
                self._total_land_mass += point.oil_mass

        self.spreading_engine.spread_oil_points(self._total_mass)
        empty_points = [coord for coord, point in self._world.items() if not point.contain_oil()]
        for point in empty_points:
            del self._world[point]
            self.points_removed.add(point)
        self._update_points_color(minimal_oil_to_show)
        self._total_time += self.timestep
        self.save_checkpoint()

    def _update_points_color(self, minimal_oil_to_show: float):
        for coord in self._world.keys():
            if changed_color(minimal_oil_to_show, self._world[coord]):
                self.points_changed.add(coord)

    def _update_oil_points(self):
        for coord in list(self._world.keys()):  # copy because dict changes size during iteration
            evaporated, dispersed = self._world[coord].update()
            self._evaporated_oil += evaporated
            self._dispersed_oil += dispersed

    def add_oil_sources(self, oil_sources: list[dict[str, Any]]):
        for oil_source in oil_sources:
            self._add_oil_source(get_xy_from_coord_raw(oil_source["coord"][1], oil_source["coord"][0]),
                                 oil_source["mass_per_minute"],
                                 oil_source["spill_start"],
                                 oil_source["spill_end"])

    def _add_oil_source(self, coord: Coord_t, mass_per_minute: float, spill_start: pd.Timestamp,
                        spill_end: pd.Timestamp):
        self._constant_sources.append((coord, mass_per_minute, spill_start, spill_end))

    def _pour_from_sources(self):
        current_timestamp = InitialValues.simulation_initial_parameters.time.min + pd.Timedelta(
            seconds=self._total_time)
        for spill in self._constant_sources:
            cords, mass_per_minute, spill_start, spill_end = spill
            if spill_start <= current_timestamp <= spill_end:
                if cords not in self._world and 0 <= cords[0] < InitialValues.point_side_lon_count and 0 <= cords[
                    1] < InitialValues.point_side_lat_count:
                    self._world[cords] = Point(cords, self)
                    self.points_changed.add(cords)
                self._world[cords].add_oil(mass_per_minute * self.timestep / 60)

    def get_topography(self, coord: Coord_t) -> TopographyState:
        if coord in self.lands:
            return TopographyState.LAND
        return TopographyState.SEA

    def get_oil_amounts(self):
        return self._total_mass - self._total_land_mass, self._total_land_mass

    def save_checkpoint(self, on_demand: bool = False):
        if on_demand or self.checkpoint_frequency > 0 and (
                self._total_time / self.timestep) % self.checkpoint_frequency == 0:
            save_to_json(self)

    @property
    def world(self):
        return self._world

    @world.setter
    def world(self, world: dict[Coord_t, Point]):
        self._world = world
        Point.world = world

    @property
    def simulation_image(self):
        return self._simulation_image

    @simulation_image.setter
    def simulation_image(self, simulation_image: Image):
        self._simulation_image = simulation_image

    @property
    def total_time(self):
        return self._total_time

    @property
    def evaporated_oil(self):
        return self._evaporated_oil

    @property
    def dispersed_oil(self):
        return self._dispersed_oil

    @property
    def constant_sources(self):
        return self._constant_sources
