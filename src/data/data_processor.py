from enum import Enum
from os import PathLike
import pandas as pd

from utilities import dataframe_replace_applay, great_circle_distance
from measurment_data import CertainMeasurment, Coordinates, SpeedMeasure


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
    coordinate = "coord"
    time_stamp = "time"
    wind = "wind"
    current = "current"


class SimpleDataProcessorImpl:
    '''
    For now just load everything into memory
    and dynamicly search for nearest data
    I will change that when needed 
    '''

    def __init__(self, csv_paths: list[PathLike]):
        self._data = self._load_all_data(csv_paths)
        self._stations_coordinates = self._get_stations_coordinates()

    def get_nearest(self, coordinates: Coordinates, time_stamp: pd.Timestamp) -> CertainMeasurment:
        nearest_coordinates = self._get_nearest_coordinates(coordinates)
        return self._get_certain_measurment(nearest_coordinates, time_stamp)

    def _get_certain_measurment(self, coordinates: Coordinates, time_stamp: pd.Timestamp) -> CertainMeasurment:
        return CertainMeasurment(
            wind=self._get_wind(coordinates, time_stamp),
            current=self._get_current(coordinates, time_stamp)
        )

    def _get_wind(self, coordinates: Coordinates, time_stamp: pd.Timestamp) -> SpeedMeasure:
        wind_for_station = self._get_wind_for_station(coordinates)
        time_index = self._get_time_index(wind_for_station, time_stamp)
        return wind_for_station.loc[time_index][DataAggregatesDecriptior.wind.value]

    def _get_current(self, coordinates: Coordinates, time_stamp: pd.Timestamp) -> SpeedMeasure:
        current_for_station = self._get_current_for_station(coordinates)
        time_index = self._get_time_index(current_for_station, time_stamp)
        return current_for_station.loc[time_index][DataAggregatesDecriptior.current.value]

    def _get_time_index(self, data: pd.DataFrame, time_stamp: pd.Timestamp) -> int:
        return (
            data[DataAggregatesDecriptior.time_stamp.value]
            .map(lambda ts: (ts - time_stamp).total_seconds())
            .idxmin()
        )

    def _get_current_for_station(self, coordinates: Coordinates) -> pd.Series:
        station_data = self._get_station_data(coordinates)
        return station_data[[DataAggregatesDecriptior.time_stamp.value, DataAggregatesDecriptior.current.value]].dropna()

    def _get_wind_for_station(self, coordinates: Coordinates) -> pd.Series:
        station_data = self._get_station_data(coordinates)
        return station_data[[DataAggregatesDecriptior.time_stamp.value, DataAggregatesDecriptior.wind.value]].dropna()

    def _get_station_data(self, coordinates: Coordinates) -> pd.DataFrame:
        return self._data[self._data[DataAggregatesDecriptior.coordinate.value] == coordinates]

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
            result_column=DataAggregatesDecriptior.coordinate.value,
            function=Coordinates,
            columns=[
                DataDescriptor.LATITUDE.value,
                DataDescriptor.LONGITUDE.value
            ]
        )

    def _data_agg_time(self, data: pd.DataFrame):
        dataframe_replace_applay(
            dataframe=data,
            result_column=DataAggregatesDecriptior.time_stamp.value,
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
            result_column=DataAggregatesDecriptior.wind.value,
            function=SpeedMeasure,
            columns=[
                DataDescriptor.WIND_SPEED.value,
                DataDescriptor.WIND_DIRECTION.value
            ]
        )

    def _data_agg_current(self, data: pd.DataFrame):
        dataframe_replace_applay(
            dataframe=data,
            result_column=DataAggregatesDecriptior.current.value,
            function=SpeedMeasure,
            columns=[
                DataDescriptor.CURRENT_SPEED.value,
                DataDescriptor.CURRENT_DIRECTION.value
            ]
        )

    def _get_stations_coordinates(self) -> pd.Series:
        return self._data[DataAggregatesDecriptior.coordinate.value].drop_duplicates().dropna()

    def _get_nearest_coordinates(self, coordinates: Coordinates) -> Coordinates:
        return self._stations_coordinates.iloc[self._stations_coordinates.map(lambda row: great_circle_distance(row, coordinates)).idxmin()]


class DataProcessor:
    def __init__(self, *args):
        self._impl = SimpleDataProcessorImpl(*args)

    def get_nearest(self, coordinates: Coordinates, time_stamp: pd.Timestamp) -> CertainMeasurment:
        return self._impl.get_nearest(coordinates, time_stamp)


class DataValidator:
    def __init__(self):
        pass

    def validate(self, csv_path: PathLike):
        pass


class DataValidationException(Exception):
    pass


class DataReader:
    def __init__(self):
        self._data_validator = DataValidator()
        self._dataset_paths = []

    def add_data(self, csv_path: PathLike):
        self._data_validator.validate(csv_path)
        self._dataset_paths.append(csv_path)

    def add_all_from_dir(self, dir_path: PathLike):
        CSV_EXT = ".csv"
        for csv_path in dir_path.glob(CSV_EXT):
            self.add_data(csv_path)

    def load_into_memory(self) -> DataProcessor:
        return DataProcessor(self._dataset_paths)


if __name__ == "__main__":

    # DataReader - i guess we need to have initial window in gui when user will provide path(s) to data
    # I'm not sure how we gonna do it so i want to provide interface that takes some input path(s) and returns DataHolder
    # where DataHolder already has (maybe) all data loaded into memory? or at least have enought information
    # for returning complete! data of measurment (already interpolated, without missing values, etc.)
    # neearest to given coordinates and time stamp

    import os

    sym_data_reader = DataReader()

    try:
        sym_data_reader.add_data(os.path.join("data", "example_data.csv"))
    except DataValidationException as ex:
        # some error handling
        # bla bla bla
        pass

    # dunno if this is a good idea
    # maybe we neeed to by chunks? dunno how many data that will be
    sym_data = sym_data_reader.load_into_memory()

    # I thought that kinds of classes will be useful in readability of simulation code
    coordinates = Coordinates(latitude=0.0, longitude=0.0)
    time_stamp = pd.Timestamp(year=2010, month=3, day=1, hour=2, minute=10)

    # that gonna interpolate and serach for nearest data
    # measurment = sym_data.get_nearest(coordinates, time_stamp)

    print(sym_data._impl._data.head())
    print(sym_data._impl._stations_coordinates.head())

    measurment = sym_data.get_nearest(coordinates, time_stamp)
    print(measurment)
