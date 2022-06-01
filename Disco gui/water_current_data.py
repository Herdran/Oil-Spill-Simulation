import netCDF4
import numpy as np
from datetime import datetime,timedelta

# CONST ------------------------------------
DATA_PATH = "VDATUM_EC2001.nc"
TIME_START = datetime(2016,1,1,0,0)
# ------------------------------------------

class WaterCurrentData:
    def __init__(self, v, u):
        self.v = v
        self.u = u

class MeasureNode:
    def __init__(self, lon, lat):
        self.latitude = lat
        self.longitude = lon
    
def get_dataset():
    return netCDF4.Dataset(DATA_PATH, mode='r')

def get_time_from_hours(h):
     return TIME_START + timedelta(hours=int(h))


if __name__ == "__main__":
    ds = get_dataset()
    nodes_size = len(ds.variables['lat'])
    latitude_data = ds.variables['lat']
    longitude_data = ds.variables['lon']
    
    nodes = [MeasureNode(longitude_data[i], latitude_data[i]) for i in range(nodes_size)]

    

    # for n in nodes:
    #     print(n.latitude, n.longitude)


