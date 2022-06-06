import netCDF4
import math

# CONST ------------------------------------
DATA_PATH = "../VDATUM_EC2001.nc" #TODO: get it from input when program starts?
# ------------------------------------------

class WaterCurrentData:
    def __init__(self, v, u):
        self.v = v
        self.u = u

class MeasureNode:
    def __init__(self, lon, lat):
        self.latitude = lat
        self.longitude = lon
    
def __get_dataset():
    return netCDF4.Dataset(DATA_PATH, mode='r')

def __get_measurment_stations(ds):
    nodes_size = len(ds.variables['lat'])
    latitude_data = ds.variables['lat']
    longitude_data = ds.variables['lon']
    nodes = [MeasureNode(longitude_data[i], latitude_data[i]) for i in range(nodes_size)]
    return nodes

def __get_measurment_times(ds):
    time_data = ds.variables['time']
    first_measurment = time_data[0]
    return [time_data[i] - first_measurment for i in range(len(time_data))]

def __get_water_data(ds, measurment_station_count, measurments_count):
    return [[WaterCurrentData(ds.variables['v'][t,i], ds.variables['u'][t,i]) for i in range(measurment_station_count)] for t in range(measurments_count)]

def get_nearest_station(stations, lat, lon):
    return min(range(len(stations)), 
        key=lambda i: math.sqrt((stations[i].latitude - lat)**2 + ((stations[i].longitude - lon)**2))
    )

def get_data():
    ds = __get_dataset()
    measurment_stations = __get_measurment_stations(ds)
    measurment_times = __get_measurment_times(ds)
    water_data = __get_water_data(ds, len(measurment_stations), len(measurment_times))
    
    return measurment_stations, measurment_times, water_data

if __name__ == '__main__':
    stations, times, data = get_data()
    for i in range(len(stations)):
        print(f"{i} -> {stations[i].latitude}, {stations[i].longitude}")
    