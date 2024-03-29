from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from math import floor
from os import PathLike, path, listdir, mkdir
from typing import Optional

import numpy as np
import pandas as pd
from scipy.interpolate import NearestNDInterpolator

from data.generic import Range
from data.measurement_data import CertainMeasurement, Coordinates, SpeedMeasure, CoordinatesBase, average_measurement
from data.simulation_run_parameters import SimulationRunParameters
from data.utilities import dataframe_replace_apply, minutes, round_values, celcius_to_kelvins
from files import get_processed_data_path
from topology.math import coordinates_distance

logger = getLogger("data")

MINUTES_IN_HOUR = 60
SECONDS_IN_MINUTE = 60

DataStationInfo = CoordinatesBase[int]


class DataDescriptor(Enum):
    LATITUDE = "lat"
    LONGITUDE = "lon"
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"
    MINUTE = "min"
    WIND_SPEED = "wind speed"
    WIND_DIRECTION = "wind dir"
    CURRENT_SPEED = "current speed"
    CURRENT_DIRECTION = "current dir"
    TEMPERATURE = "temp"


class StationNeighbourType(Enum):
    NORTH = DataStationInfo(longitude=0, latitude=-1)
    SOUTH = DataStationInfo(longitude=0, latitude=1)
    WEST = DataStationInfo(longitude=-1, latitude=0)
    EAST = DataStationInfo(longitude=1, latitude=0)
    NORTH_WEST = DataStationInfo(longitude=-1, latitude=-1)
    NORTH_EAST = DataStationInfo(longitude=1, latitude=-1)
    SOUTH_WEST = DataStationInfo(longitude=-1, latitude=1)
    SOUTH_EAST = DataStationInfo(longitude=1, latitude=1)
    CENTER = DataStationInfo(longitude=0, latitude=0)

    def get_interpolation_neighbours(self) -> Optional[list['StationNeighbourType']]:
        return INTERPOLATION_NEIGHBOURS.get(self)


INTERPOLATION_NEIGHBOURS = {
    StationNeighbourType.NORTH_WEST: [StationNeighbourType.NORTH, StationNeighbourType.CENTER,
                                      StationNeighbourType.WEST, StationNeighbourType.NORTH_WEST],
    StationNeighbourType.NORTH_EAST: [StationNeighbourType.NORTH, StationNeighbourType.CENTER,
                                      StationNeighbourType.EAST, StationNeighbourType.NORTH_EAST],
    StationNeighbourType.SOUTH_WEST: [StationNeighbourType.SOUTH, StationNeighbourType.CENTER,
                                      StationNeighbourType.WEST, StationNeighbourType.SOUTH_WEST],
    StationNeighbourType.SOUTH_EAST: [StationNeighbourType.SOUTH, StationNeighbourType.CENTER,
                                      StationNeighbourType.EAST, StationNeighbourType.SOUTH_EAST]
}


class DataAggregationDescriptor(Enum):
    LATITUDE = "lat"
    LONGITUDE = "lon"
    TIME_STAMP = "time"
    WIND_N = "wind_n"
    WIND_E = "wind_e"
    CURRENT_N = "current_n"
    CURRENT_E = "current_e"
    TEMPERATURE = "temp"


@dataclass
class LoadedData:
    measurements_data: dict

    @staticmethod
    def from_dataframe(data: pd.DataFrame) -> 'LoadedData':
        get_measurement = lambda row: CertainMeasurement(
            wind=SpeedMeasure(row.wind_n, row.wind_e),
            current=SpeedMeasure(row.current_n, row.current_e),
            temperature=row.temp
        )

        return LoadedData({(row.time, row.lat, row.lon): get_measurement(row) for row in data.itertuples()})

    def try_get_measurement(self, time: float, latitude: float, longitude: float) -> SpeedMeasure:
        measure = self.measurements_data.get((time, latitude, longitude))

        if measure is None:
            logger.warning(
                f"can't parse measurement for given coordinates {(latitude, longitude)} and time stamp {time}")
            DEFAULT_SPEED = SpeedMeasure(0, 0)
            DEFAULT_TEMPERATURE = 302.15
            return CertainMeasurement(DEFAULT_SPEED, DEFAULT_SPEED, DEFAULT_TEMPERATURE)

        return measure


class DataProcessorImpl:
    def __init__(self, csv_paths: list[PathLike], simulation_run_parameters: SimulationRunParameters):
        logger.debug("STARTED: Preprocessing data...")

        self.loaded_data: dict[int, pd.DataFrame] = {}

        self.run_parameters = simulation_run_parameters
        data = self._load_all_data(csv_paths)

        time_points = self._create_environment_time_range(simulation_run_parameters)
        self.latitude_points = self._create_environment_latitude_range(simulation_run_parameters)
        self.longitude_points = self._create_environment_longitude_range(simulation_run_parameters)

        self.latitude_points = round_values(self.latitude_points)
        self.longitude_points = round_values(self.longitude_points)

        self.min_coords = Coordinates(
            latitude=min(self.latitude_points),
            longitude=min(self.longitude_points)
        )

        self.coord_range = CoordinatesBase(
            latitude=(max(self.latitude_points) - min(
                self.latitude_points)) / simulation_run_parameters.interpolation_grid_size.latitude,
            longitude=(max(self.longitude_points) - min(
                self.longitude_points)) / simulation_run_parameters.interpolation_grid_size.longitude
        )

        time_points, latitude_points, longitude_points = np.meshgrid(time_points, self.latitude_points,
                                                                     self.longitude_points)

        points_wind_n, values_wind_n = self._get_interpolation_area(data, DataAggregationDescriptor.WIND_N,
                                                                    DataAggregationDescriptor.WIND_E)
        wind_n_interpolated = self._get_interpolated_data(time_points, latitude_points, longitude_points, points_wind_n,
                                                          values_wind_n)

        points_wind_e, values_wind_e = self._get_interpolation_area(data, DataAggregationDescriptor.WIND_E,
                                                                    DataAggregationDescriptor.WIND_N)
        wind_e_interpolated = self._get_interpolated_data(time_points, latitude_points, longitude_points, points_wind_e,
                                                          values_wind_e)

        points_current_n, values_current_n = self._get_interpolation_area(data, DataAggregationDescriptor.CURRENT_N,
                                                                          DataAggregationDescriptor.CURRENT_E)
        current_n_interpolated = self._get_interpolated_data(time_points, latitude_points, longitude_points,
                                                             points_current_n, values_current_n)

        points_current_e, values_current_e = self._get_interpolation_area(data, DataAggregationDescriptor.CURRENT_E,
                                                                          DataAggregationDescriptor.CURRENT_N)
        current_e_interpolated = self._get_interpolated_data(time_points, latitude_points, longitude_points,
                                                             points_current_e, values_current_e)

        points_temp, values_temp = self._get_interpolation_area(data, DataAggregationDescriptor.TEMPERATURE)
        values_temp = np.vectorize(celcius_to_kelvins)(values_temp)
        temp_interpolated = self._get_interpolated_data(time_points, latitude_points, longitude_points, points_temp,
                                                        values_temp)

        environment_area = pd.DataFrame(
            {
                DataAggregationDescriptor.TIME_STAMP.value: time_points.flatten(),
                DataAggregationDescriptor.LATITUDE.value: latitude_points.flatten(),
                DataAggregationDescriptor.LONGITUDE.value: longitude_points.flatten(),
                DataAggregationDescriptor.WIND_N.value: wind_n_interpolated.flatten(),
                DataAggregationDescriptor.WIND_E.value: wind_e_interpolated.flatten(),
                DataAggregationDescriptor.CURRENT_N.value: current_n_interpolated.flatten(),
                DataAggregationDescriptor.CURRENT_E.value: current_e_interpolated.flatten(),
                DataAggregationDescriptor.TEMPERATURE.value: temp_interpolated.flatten()
            }
        )

        environment_area.sort_values(inplace=True, by=[DataAggregationDescriptor.TIME_STAMP.value])

        logger.debug("FINISHED: Preprocessing data...")
        path_to_save = get_processed_data_path()
        if not path.exists(path_to_save):
            logger.debug(f"Creating directory {path_to_save}")
            mkdir(path_to_save)
        logger.debug(f"STARTED: Saving preprocessed data to {path_to_save}...")

        # TODO: code below is a mess probably need to be refactored in the future
        to_save = pd.DataFrame()

        hour = 0
        last_minutes = -1

        get_data_path = lambda: path.join(path_to_save, f"{hour}.csv")

        for _, row in environment_area.iterrows():
            time = row[DataAggregationDescriptor.TIME_STAMP.value]
            if time > 0 and time % MINUTES_IN_HOUR == 0 and last_minutes != time:
                to_save.to_csv(get_data_path(), index=False)
                to_save = pd.DataFrame()
                logger.info(f"saved: {hour} hour")
                hour += 1
            last_minutes = time
            to_save = pd.concat([to_save, pd.DataFrame([row])], ignore_index=True)
        to_save.to_csv(get_data_path(), index=False)
        logger.info(f"saved: {hour} hour")

        logger.debug("FINISHED: Saving preprocessed data...")

    def should_update_data(self, time_from_last_update: pd.Timedelta) -> bool:
        return time_from_last_update > self.run_parameters.data_time_step

    def get_measurement(self, coordinates: Coordinates, nearest_station_info: DataStationInfo,
                        time_stamp: pd.Timestamp) -> CertainMeasurement:
        SHOULD_INTERPOLATE = False

        loaded_data = self._get_data_for_time(time_stamp)
        time_stamp = self._get_nearest_data_time(time_stamp)

        station_coordinates = self._get_coord_for_station(nearest_station_info)

        if not SHOULD_INTERPOLATE or coordinates == station_coordinates:
            return self._get_certain_measurement(loaded_data, station_coordinates, time_stamp)

        interpolation_neighbours = self._get_direction_of_station(coordinates,
                                                                  station_coordinates).get_interpolation_neighbours()
        neighbours_stations_info = self._get_neighbours_station_info(interpolation_neighbours, nearest_station_info)
        neighbours_stations_coords = [self._get_coord_for_station(station_info) for station_info in
                                      neighbours_stations_info]
        weights = [coordinates_distance(coordinates, coord) for coord in neighbours_stations_coords]
        measurements = [self._get_certain_measurement(loaded_data, coord, time_stamp) for coord in
                        neighbours_stations_coords]

        return CertainMeasurement(
            wind=SpeedMeasure.from_average([measurement.wind for measurement in measurements], weights),
            current=SpeedMeasure.from_average([measurement.current for measurement in measurements], weights),
            temperature=average_measurement([measurement.temperature for measurement in measurements], weights)
        )

    def _get_coord_for_station(self, station_info: DataStationInfo) -> Coordinates:
        return Coordinates(
            self.latitude_points[station_info.latitude],
            self.longitude_points[station_info.longitude]
        )

    def _get_neighbours_station_info(self, interpolation_neighbours: list['StationNeighbourType'],
                                     nearest_station_info: DataStationInfo) -> list[DataStationInfo]:
        result = []
        for neighbour_type in interpolation_neighbours:
            station_info_opt = self._neighbour_station_info(nearest_station_info, neighbour_type)
            if station_info_opt is not None:
                result.append(station_info_opt)
        return result

    def _get_direction_of_station(self, coordinates: Coordinates,
                                  station_coordinates: Coordinates) -> StationNeighbourType:
        lat_diff = (
            StationNeighbourType.NORTH if coordinates.latitude > station_coordinates.latitude else StationNeighbourType.SOUTH).value.latitude
        lon_diff = (
            StationNeighbourType.EAST if coordinates.longitude > station_coordinates.longitude else StationNeighbourType.WEST).value.longitude
        return StationNeighbourType(DataStationInfo(lat_diff, lon_diff))

    def _neighbour_station_info(self, station_info: DataStationInfo, neighbour_type: StationNeighbourType) -> Optional[
        DataStationInfo]:
        lat_candidate = station_info.latitude + neighbour_type.value.latitude
        lon_candidate = station_info.longitude + neighbour_type.value.longitude

        MIN_COORD = 0
        if (not (MIN_COORD <= lat_candidate < self.run_parameters.interpolation_grid_size.latitude) or
                not (MIN_COORD <= lon_candidate < self.run_parameters.interpolation_grid_size.longitude)):
            return None

        return DataStationInfo(lat_candidate, lon_candidate)

    def _get_certain_measurement(self, data: LoadedData, coordinates: Coordinates,
                                 time_stamp: pd.Timestamp) -> CertainMeasurement:
        delta = minutes(time_stamp - self.run_parameters.time.min)
        return data.try_get_measurement(delta, coordinates.latitude, coordinates.longitude)

    def _get_nearest_data_time(self, time_stamp: pd.Timestamp) -> pd.Timestamp:
        duration_till_start = time_stamp - self.run_parameters.time.min
        time_stamps_passed = duration_till_start / self.run_parameters.data_time_step
        return self.run_parameters.time.min + (floor(time_stamps_passed) * self.run_parameters.data_time_step)

    def _get_data_for_time(self, time_stamp: pd.Timestamp) -> LoadedData:
        needed_hour = self._get_run_hour_for_time_stamp(time_stamp)

        if len(self.loaded_data) == 0:
            self._load_data_for_time(needed_hour)

        first_loaded_hour = next(iter(self.loaded_data.keys()))
        if needed_hour > first_loaded_hour:
            self.loaded_data.pop(first_loaded_hour)
            return self._get_data_for_time(time_stamp)

        # TODO: preloading next data <- could be done in another process?
        PRELOAD_FACTOR = 2
        ONLY_ONE_HOUR_LEFT_COUNT = 1
        if len(self.loaded_data) == ONLY_ONE_HOUR_LEFT_COUNT and (
                time_stamp + (self.run_parameters.data_time_step / PRELOAD_FACTOR)).hour > time_stamp.hour:
            self._load_data_for_time(first_loaded_hour + 1)

        return next(iter(self.loaded_data.values()))

    def _get_run_hour_for_time_stamp(self, time_stamp: pd.Timestamp) -> int:
        SECONDS_IN_HOUR = 3600
        return int((time_stamp - self.run_parameters.time.min).total_seconds()) // SECONDS_IN_HOUR

    def _load_data_for_time(self, simulation_hour: int) -> None:
        read_data = self._read_data_for_time(simulation_hour)
        if read_data is not None:
            self.loaded_data[simulation_hour] = LoadedData.from_dataframe(read_data)

    def _read_data_for_time(self, simulation_hour: int) -> Optional[pd.DataFrame]:
        logger.debug(f"Reading data for hour {simulation_hour}")
        data_path = path.join(get_processed_data_path(), f"{simulation_hour}.csv")
        return pd.read_csv(data_path) if path.exists(data_path) else None

    def _get_interpolated_data(self, time_points: np.array, latitude_points: np.array, longitude_points: np.array,
                               points: np.array, values: np.array) -> np.array:
        interpolator = NearestNDInterpolator(points, values)
        return interpolator(time_points, latitude_points, longitude_points)

    def _get_interpolation_area(self, data: pd.DataFrame, column_filter: DataAggregationDescriptor,
                                additional_filter: DataAggregationDescriptor = None) -> tuple[np.ndarray, np.ndarray]:
        points: list[list] = []
        values: list[float] = []

        if additional_filter is not None:
            data_with_column = data[data[column_filter.value].notna() & data[additional_filter.value].notna()]
        else:
            data_with_column = data[data[column_filter.value].notna()]

        for _, row in data_with_column.iterrows():
            lat = row[DataAggregationDescriptor.LATITUDE.value]
            lon = row[DataAggregationDescriptor.LONGITUDE.value]
            time = row[DataAggregationDescriptor.TIME_STAMP.value]
            time_from_start = minutes(time - self.run_parameters.time.min)
            points.append((time_from_start, lat, lon))
            values.append(row[column_filter.value])

        return np.array(points), np.array(values)

    def _create_environment_latitude_range(self, simulation_run_parameters: SimulationRunParameters) -> np.array:
        latitude_range = Range(simulation_run_parameters.area.min.latitude, simulation_run_parameters.area.max.latitude)
        latitude_step = (
                                latitude_range.max - latitude_range.min) / simulation_run_parameters.interpolation_grid_size.latitude
        return np.array([latitude_range.min + i * latitude_step for i in
                         range(simulation_run_parameters.interpolation_grid_size.latitude)])

    def _create_environment_longitude_range(self, simulation_run_parameters: SimulationRunParameters) -> np.array:
        longitude_range = Range(simulation_run_parameters.area.min.longitude,
                                simulation_run_parameters.area.max.longitude)
        longitude_step = (
                                 longitude_range.max - longitude_range.min) / simulation_run_parameters.interpolation_grid_size.longitude
        return np.array([longitude_range.min + i * longitude_step for i in
                         range(simulation_run_parameters.interpolation_grid_size.longitude)])

    def _create_environment_time_range(self, simulation_run_parameters: SimulationRunParameters) -> np.array:
        time_range = simulation_run_parameters.time
        time_step = simulation_run_parameters.data_time_step
        times_count = int((time_range.max - time_range.min) / time_step)
        return np.array([minutes(i * time_step) for i in range(times_count)])

    def _load_single_dataset(self, csv_path: PathLike) -> pd.DataFrame:
        return pd.read_csv(csv_path)

    def _load_all_data(self, csv_paths: list[PathLike]) -> pd.DataFrame:
        concatenated_data = pd.concat([self._load_single_dataset(csv_path)
                                       for csv_path in csv_paths])
        self._data_agg_wind(concatenated_data)
        self._data_agg_current(concatenated_data)
        self._data_agg_time(concatenated_data)

        return concatenated_data

    def _data_agg_time(self, data: pd.DataFrame):
        def get_time_stamp(*args):
            return pd.Timestamp(*[int(arg) for arg in args])

        dataframe_replace_apply(
            dataframe=data,
            result_columns=[DataAggregationDescriptor.TIME_STAMP.value],
            function=get_time_stamp,
            columns=[
                DataDescriptor.YEAR.value,
                DataDescriptor.MONTH.value,
                DataDescriptor.DAY.value,
                DataDescriptor.HOUR.value,
                DataDescriptor.MINUTE.value
            ]
        )

    def _data_agg_wind(self, data: pd.DataFrame):
        dataframe_replace_apply(
            dataframe=data,
            result_columns=[DataAggregationDescriptor.WIND_N.value, DataAggregationDescriptor.WIND_E.value],
            function=SpeedMeasure.from_direction,
            columns=[
                DataDescriptor.WIND_SPEED.value,
                DataDescriptor.WIND_DIRECTION.value
            ]
        )

    def _data_agg_current(self, data: pd.DataFrame):
        dataframe_replace_apply(
            dataframe=data,
            result_columns=[DataAggregationDescriptor.CURRENT_N.value, DataAggregationDescriptor.CURRENT_E.value],
            function=SpeedMeasure.from_direction,
            columns=[
                DataDescriptor.CURRENT_SPEED.value,
                DataDescriptor.CURRENT_DIRECTION.value
            ]
        )

    def weather_station_coordinates(self, coordinates: Coordinates) -> DataStationInfo:
        coords = CoordinatesBase(
            latitude=max(0, coordinates.latitude - self.min_coords.latitude),
            longitude=max(0, coordinates.longitude - self.min_coords.longitude)
        )

        return DataStationInfo(
            latitude=min(self.run_parameters.interpolation_grid_size.latitude - 1,
                         floor(coords.latitude / self.coord_range.latitude)),
            longitude=min(self.run_parameters.interpolation_grid_size.longitude - 1,
                          floor(coords.longitude / self.coord_range.longitude))
        )


class DataProcessor:
    def __init__(self, *args):
        self._impl = DataProcessorImpl(*args)

    def get_measurement(self, coordinates: Coordinates, nearest_station_info: DataStationInfo,
                        time_stamp: pd.Timestamp) -> CertainMeasurement:
        return self._impl.get_measurement(coordinates, nearest_station_info, time_stamp)

    def should_update_data(self, time_from_last_update: pd.Timedelta) -> bool:
        return self._impl.should_update_data(time_from_last_update)

    def weather_station_coordinates(self, coordinates: Coordinates) -> DataStationInfo:
        return self._impl.weather_station_coordinates(coordinates)


class DataValidationException(Exception):
    pass


class DataValidator:
    def __init__(self):
        pass

    def validate(self, csv_path: PathLike):
        if not path.isfile(csv_path):
            raise DataValidationException(f"File '{csv_path}' does not exist!.")
        self.check_columns(csv_path)

    def validate_dir(self, data_dir_path: PathLike):
        if not path.isdir(data_dir_path):
            raise DataValidationException(f"Directory '{data_dir_path}' does not exist!.")

    def check_columns(self, csv_path: PathLike):
        try:
            file = pd.read_csv(csv_path)
        except Exception as e:
            raise DataValidationException(f"File {csv_path} is not a valid csv file: {e}")
        columns = file.columns
        for column in DataDescriptor:
            if column.value not in columns:
                raise DataValidationException(f"File {csv_path} does not contain all required columns - {column.value}")


class DataReader:
    def __init__(self):
        self._data_validator = DataValidator()
        self._dataset_paths = []

    def add_data(self, csv_path: PathLike):
        self._data_validator.validate(csv_path)
        self._dataset_paths.append(csv_path)
        logger.debug(f"Added data from file: {csv_path}")

    def add_all_from_dir(self, dir_path: PathLike):
        CSV_EXT = ".csv"
        IS_CSV = lambda file: file.endswith(CSV_EXT)

        self._data_validator.validate_dir(dir_path)
        for file in filter(IS_CSV, listdir(dir_path)):
            self.add_data(path.join(dir_path, file))

    def preprocess(self, simulation_run_parameters: SimulationRunParameters) -> DataProcessor:
        return DataProcessor(self._dataset_paths, simulation_run_parameters)
