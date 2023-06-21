import datetime
from enum import Enum
from math import floor
from os import PathLike
from typing import Callable, Optional
import numpy as np
import pandas as pd
from scipy.interpolate import NearestNDInterpolator

from generic import Range
from utilities import dataframe_replace_applay, great_circle_distance, minutes
from measurment_data import CertainMeasurment, CoordinatesBase, Coordinates, SpeedMeasure
from simulation_run_parameters import SimulationRunParameters, CellSideCount


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


class DataAggregatesDecriptior(Enum):
    COORDINATE = "coord"
    TIME_STAMP = "time"
    WIND = "wind"
    CURRENT = "current"


class DataProcessorImpl:
    def __init__(self, csv_paths: list[PathLike], simulation_run_parameters: SimulationRunParameters):
        self.loaded_data: dict[int, pd.DataFrame] = {}
        
        self.run_parameters = simulation_run_parameters
        data = self._load_all_data(csv_paths)      
        
        time_points = self._create_envirement_time_range(simulation_run_parameters)
        latitude_points = self._create_envirement_latitude_range(simulation_run_parameters)
        longitude_points = self._create_envirement_longitude_range(simulation_run_parameters)
    
        time_points, latitude_points, longitude_points = np.meshgrid(time_points, latitude_points, longitude_points)
        
        points_wind_n, values_wind_n = self._get_interpolation_area(data, DataAggregatesDecriptior.WIND, lambda row: row[DataAggregatesDecriptior.WIND.value].speed_north)
        wind_n_interpolated = self._get_interpolated__data(time_points, latitude_points, longitude_points, points_wind_n, values_wind_n)
        
        points_wind_e, values_wind_e = self._get_interpolation_area(data, DataAggregatesDecriptior.WIND, lambda row: row[DataAggregatesDecriptior.WIND.value].speed_east)
        wind_e_interpolated = self._get_interpolated__data(time_points, latitude_points, longitude_points, points_wind_e, values_wind_e)
        
        points_current_n, values_current_n = self._get_interpolation_area(data, DataAggregatesDecriptior.CURRENT, lambda row: row[DataAggregatesDecriptior.CURRENT.value].speed_north)
        current_n_interpolated = self._get_interpolated__data(time_points, latitude_points, longitude_points, points_current_n, values_current_n)
        
        points_current_e, values_current_e = self._get_interpolation_area(data, DataAggregatesDecriptior.CURRENT, lambda row: row[DataAggregatesDecriptior.CURRENT.value].speed_east)
        current_e_interpolated = self._get_interpolated__data(time_points, latitude_points, longitude_points, points_current_e, values_current_e)
        
        
        # into one dataframe
        envirement_area = pd.DataFrame(
            {
                DataAggregatesDecriptior.TIME_STAMP.value: time_points.flatten(),
                DataAggregatesDecriptior.COORDINATE.value : [Coordinates(latitude, longitude) for latitude, longitude in zip(latitude_points.flatten(), longitude_points.flatten())],
                DataAggregatesDecriptior.WIND.value: [SpeedMeasure(wind_n, wind_e) for wind_n, wind_e in zip(wind_n_interpolated.flatten(), wind_e_interpolated.flatten())],
                DataAggregatesDecriptior.CURRENT.value: [SpeedMeasure(current_n, current_e) for current_n, current_e in zip(current_n_interpolated.flatten(), current_e_interpolated.flatten())]
            }
        )
        
        envirement_area.sort_values(inplace=True, by=[DataAggregatesDecriptior.TIME_STAMP.value])

        path_to_save = self.run_parameters.path_to_data
        MINUTES_IN_HOUR = 60

        to_save = pd.DataFrame()
        
        hour = 0
        last_minutes = -1
        
        get_data_path = lambda: os.path.join(path_to_save, f"{hour}.csv")
        
        for _, row in envirement_area.iterrows():
            time = row[DataAggregatesDecriptior.TIME_STAMP.value]
            if time > 0 and time % MINUTES_IN_HOUR == 0 and last_minutes != time:
                to_save.to_csv(get_data_path(), index=False)
                to_save = pd.DataFrame()
                print(f"saved: {hour} hour")
                hour += 1
            last_minutes = time
            to_save = pd.concat([to_save, pd.DataFrame([row])], ignore_index=True)
        to_save.to_csv(get_data_path(), index=False)
        print(f"saved: {hour} hour")
        

    def get_nearest(self, coordinates: Coordinates, time_stamp: pd.Timestamp) -> CertainMeasurment:
        # TODO: check if input is correct e.g. time_stamp is in range of simulation
        
        data = self._get_data_for_time(time_stamp)
        time_stamp = self._get_nearest_data_time(time_stamp)
        coordinates = self._get_nearest_data_coordinates(coordinates)
        return self._get_certain_measurment(data, coordinates, time_stamp)
    
    def _get_measurment_row_data(self, data: pd.DataFrame, coordinates: Coordinates, time_stamp: pd.Timestamp) -> pd.Series:
        SECONDS_IN_MINUTE = 60
        duration_till_start = (time_stamp - self.run_parameters.time.min).seconds // SECONDS_IN_MINUTE
        
        
        row =  data[
            (data[DataAggregatesDecriptior.TIME_STAMP.value] == duration_till_start) & 
            (data[DataAggregatesDecriptior.COORDINATE.value] == str(coordinates))
        ]
        
        return row.iloc[0]
        
        

    def _get_certain_measurment(self, data: pd.DataFrame, coordinates: Coordinates, time_stamp: pd.Timestamp) -> CertainMeasurment:
        row = self._get_measurment_row_data(data, coordinates, time_stamp)
        return CertainMeasurment(
            wind=row[DataAggregatesDecriptior.WIND.value],
            current=row[DataAggregatesDecriptior.CURRENT.value]
        )

    def _get_nearest_data_time(self, time_stamp: pd.Timestamp) -> pd.Timestamp:
        duration_till_start = time_stamp - self.run_parameters.time.min
        time_smamps_passed = duration_till_start / self.run_parameters.data_time_step
        return self.run_parameters.time.min + (floor(time_smamps_passed) * self.run_parameters.data_time_step)
    
    def _get_nearest_data_coordinates(self, coordinates: Coordinates) -> Coordinates:
        # for now just asume that coordinates are exacly like preprocessed
        # TODO: somehow get closest coordinates that are for sure in data
        return coordinates 
    
    def _get_data_for_time(self, time_stamp: pd.Timestamp) -> Optional[pd.DataFrame]:
        needed_hour = self._get_run_hour_for_time_stamp(time_stamp)
        
        if len(self.loaded_data) == 0:
            self._load_data_for_time(needed_hour)
        
        
        first_loaded_hour = next(iter(self.loaded_data.keys()))
        if needed_hour > first_loaded_hour:
            self.loaded_data.pop(first_loaded_hour)
            return self._get_data_for_time(time_stamp)
        
        # preloading next data <- could be done in another process?
        preload_factor = 2
        if (time_stamp + (self.run_parameters.data_time_step / preload_factor)).hour  > time_stamp.hour:
            self._load_data_for_time(first_loaded_hour + 1)
            
        return next(iter(self.loaded_data.values()))
    
    def _get_run_hour_for_time_stamp(self, time_stamp: pd.Timestamp) -> int:
        SECONDS_IN_HOUR = 3600
        return (time_stamp - self.run_parameters.time.min).seconds // SECONDS_IN_HOUR
        
    def _load_data_for_time(self, simulation_hour: int) -> None:
        readed_data = self._read_data_for_time(simulation_hour)
        if readed_data is not None:
            self.loaded_data[simulation_hour] = readed_data
        
    def _read_data_for_time(self, simulation_hour: int) -> Optional[pd.DataFrame]:
        path = os.path.join(self.run_parameters.path_to_data, f"{simulation_hour}.csv")
        return pd.read_csv(path) if os.path.exists(path) else None

    def _get_interpolated__data(self, time_points: np.array, latitude_points: np.array, longitude_points: np.array, points: np.array, values: np.array) -> np.array:
        interpolator = NearestNDInterpolator(points, values)
        return interpolator(time_points, latitude_points, longitude_points)
        
    def _get_interpolation_area(self, data: pd.DataFrame, column_filter: DataAggregatesDecriptior, value_getter: Callable[[pd.Series], float]) -> tuple[np.ndarray, np.ndarray]:
        points: list[list] = []
        values: list[float] = []
        
        data_with_column = data[data[column_filter.value].notna()]
        
        for _, row in data_with_column.iterrows():
            coord = row[DataAggregatesDecriptior.COORDINATE.value]
            time = row[DataAggregatesDecriptior.TIME_STAMP.value]
            time_from_start = minutes(time - self.run_parameters.time.min)
            points.append((time_from_start, coord.latitude, coord.longitude))
            values.append(value_getter(row))
        
        return np.array(points), np.array(values)
        
        
    def _create_envirement_latitude_range(self, simulation_run_parameters: SimulationRunParameters) -> np.array:
        latitude_range = Range(simulation_run_parameters.area.min.latitude, simulation_run_parameters.area.max.latitude)
        latitude_step = (latitude_range.max - latitude_range.min) / simulation_run_parameters.cells_side_count.latitude
        return np.array([latitude_range.min + i * latitude_step for i in range(simulation_run_parameters.cells_side_count.latitude)])
        
    def _create_envirement_longitude_range(self, simulation_run_parameters: SimulationRunParameters) -> np.array:
        longitude_range = Range(simulation_run_parameters.area.min.longitude, simulation_run_parameters.area.max.longitude)
        longitude_step = (longitude_range.max - longitude_range.min) / simulation_run_parameters.cells_side_count.longitude
        return np.array([longitude_range.min + i * longitude_step for i in range(simulation_run_parameters.cells_side_count.longitude)])
    
    def _create_envirement_time_range(self, simulation_run_parameters: SimulationRunParameters) -> np.array:
        time_range = simulation_run_parameters.time
        time_step = simulation_run_parameters.data_time_step
        times_count = int((time_range.max - time_range.min) / time_step)
        return np.array([minutes(i * time_step) for i in range(times_count)])

    def _load_single_dataset(self, csv_path: PathLike) -> pd.DataFrame:
        return pd.read_csv(csv_path)

    def _load_all_data(self, csv_paths: list[PathLike]) -> pd.DataFrame:
        concated_data = pd.concat([self._load_single_dataset(csv_path)
                                   for csv_path in csv_paths])
        self._data_agg_coordinates(concated_data)
        self._data_agg_time(concated_data)
        self._data_agg_wind(concated_data)
        self._data_agg_current(concated_data)

        return concated_data

    def _data_agg_coordinates(self, data: pd.DataFrame):
        dataframe_replace_applay(
            dataframe=data,
            result_column=DataAggregatesDecriptior.COORDINATE.value,
            function=Coordinates,
            columns=[
                DataDescriptor.LATITUDE.value,
                DataDescriptor.LONGITUDE.value
            ]
        )

    def _data_agg_time(self, data: pd.DataFrame):
        dataframe_replace_applay(
            dataframe=data,
            result_column=DataAggregatesDecriptior.TIME_STAMP.value,
            function=pd.Timestamp,
            columns=[
                DataDescriptor.YEAR.value,
                DataDescriptor.MONTH.value,
                DataDescriptor.DAY.value,
                DataDescriptor.HOUR.value,
                DataDescriptor.MINUTE.value
            ]
        )

    def _data_agg_wind(self, data: pd.DataFrame):
        dataframe_replace_applay(
            dataframe=data,
            result_column=DataAggregatesDecriptior.WIND.value,
            function=SpeedMeasure.from_direction,
            columns=[
                DataDescriptor.WIND_SPEED.value,
                DataDescriptor.WIND_DIRECTION.value
            ]
        )

    def _data_agg_current(self, data: pd.DataFrame):
        dataframe_replace_applay(
            dataframe=data,
            result_column=DataAggregatesDecriptior.CURRENT.value,
            function=SpeedMeasure.from_direction,
            columns=[
                DataDescriptor.CURRENT_SPEED.value,
                DataDescriptor.CURRENT_DIRECTION.value
            ]
        )

    def _get_stations_coordinates(self) -> pd.Series:
        return self._data[DataAggregatesDecriptior.COORDINATE.value].drop_duplicates().dropna()

    def _get_nearest_coordinates(self, coordinates: Coordinates) -> Coordinates:
        return self._stations_coordinates.iloc[self._stations_coordinates.map(lambda row: great_circle_distance(row, coordinates)).idxmin()]


class DataProcessor:
    def __init__(self, *args):
        self._impl = DataProcessorImpl(*args)

    def get_nearest(self, coordinates: Coordinates, time_stamp: pd.Timestamp) -> CertainMeasurment:
        return self._impl.get_nearest(coordinates, time_stamp)


class DataValidationException(Exception):
    pass

class DataValidator:
    def __init__(self):
        pass

    def validate(self, csv_path: PathLike):
        if not os.path.isfile(csv_path):
            raise DataValidationException("File does not exist")
        
        self.check_columns(csv_path)
        
    def check_columns(self, csv_path: PathLike):
        pd.read_csv(csv_path)
        columns = pd.read_csv(csv_path).columns
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

    def add_all_from_dir(self, dir_path: PathLike):
        CSV_EXT = ".csv"
        for file in os.listdir(dir_path):
            if file.endswith(CSV_EXT):
                self.add_data(os.path.join(dir_path, file))

    def preprocess(self, simulation_run_parameters: SimulationRunParameters) -> DataProcessor:
        return DataProcessor(self._dataset_paths, simulation_run_parameters)


if __name__ == "__main__":
    simulation_run_parameters = SimulationRunParameters(
        area=Range(
            min=Coordinates(
                latitude=50.0,
                longitude=-88.77964
            ),
            max=Coordinates(
                latitude=51.0,
                longitude=-88.72648
            )
        ),
        time=Range(
            min=pd.Timestamp("2010-04-01 00:00:00"),
            max=pd.Timestamp("2010-04-01 06:00:00"),
        ),
        data_time_step=pd.Timedelta(minutes=30),
        cells_side_count=CellSideCount(
            latitude=10,
            longitude=10
        ),
        path_to_data="data/processed_data"
    )
        
        
    # DataReader - i guess we need to have initial window in gui when user will provide path(s) to data
    # I'm not sure how we gonna do it so i want to provide interface that takes some input path(s) and returns DataHolder
    # where DataHolder already has (maybe) all data loaded into memory? or at least have enought information
    # for returning complete! data of measurment (already interpolated, without missing values, etc.)
    # neearest to given coordinates and time stamp

    import os

    sym_data_reader = DataReader()

    try:
        #sym_data_reader.add_data(os.path.join("data", "example_data.csv"))
        sym_data_reader.add_all_from_dir(os.path.join("data", "processed"))
    except DataValidationException as ex:
        # some error handling
        # bla bla bla
        pass

    # dunno if this is a good idea
    # maybe we neeed to by chunks? dunno how many data that will be
    sym_data = sym_data_reader.preprocess(simulation_run_parameters)

    coordinates = Coordinates(latitude=50.6, longitude=-88.75306)
    time_stamp = pd.Timestamp("2010-04-01 01:01:12")

    measurment = sym_data.get_nearest(coordinates, time_stamp)
    print(measurment)