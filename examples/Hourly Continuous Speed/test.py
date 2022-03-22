import numpy as np
import pandas as pd

import simscale_eba.PedestrianWindComfort as pwc
import simscale_eba.pwc_status as stat
import simscale_eba.HourlyContinuous as hc

import pathlib
import time

resolution = 5.0
project = "Outdoor Comfort Example"
simulation = "Pedestrian Wind Comfort"
run = "Run 1"

path = pathlib.Path("E:\Current Cases\Grasshopper Plugin")

sim = pwc.pedestrian_wind_comfort_results()
sim.set_resolution(resolution)
sim.get_pedestrian_wind_comfort(project, simulation, run, path=path)

sim._create_dimensional_quantities()
sim._create_dimensionless_quantities()

sim.cluster_outputs()

path = pathlib.Path(path)

pwc_status = stat.simulation_status()
pwc_status.set_result_directory(path)
pwc_status.read_simulation_status()

# Put any path here
path = r'E:\Current Cases\external-building-aerodynamics\examples\epw_to_stat\USA_MA_Boston-Logan.Intl.AP.725090_TMYx.2004-2018.epw'
epw = hc.HourlyContinuous()
epw.import_epw(pathlib.Path(path))

epw_directions = np.array(epw._hourly_direction).astype(float)
epw_speeds = np.array(epw._hourly_wind_speed)

field_paths = pwc_status.field_paths["dimensionless_UMag"]

start = time.time()
def get_speeds(direction, reference_speed, keys):
        field_path = pathlib.Path(field_paths[key])
        print(direction)
        rounded_direction = pwc.round_direction(field_path, direction)
        print(rounded_direction)
        field = pd.read_feather(field_path)[str(rounded_direction)]
        speed = (field * reference_speed).values
        print(field)
        #speeds.append(speed)
        return np.reshape(speed, (-1, 1))

mySpeedFunc = np.frompyfunc(get_speeds, 3, 1)
'''
no_hours = 8760
directions = np.random.uniform(low=0, high=360, size=(no_hours))
reference_speeds = np.random.uniform(low=2, high=30, size=(no_hours))
'''
speeds = []
for key in field_paths.keys():
    keys = np.repeat(key, len(epw_directions))
    hc_speeds = np.concatenate(mySpeedFunc(epw_directions, epw_speeds, keys), axis=1)
    
end = time.time()
print(end - start)