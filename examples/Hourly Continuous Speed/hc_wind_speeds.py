import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import simscale_eba.PedestrianWindComfort as pwc
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

# Put any path here
epw_path = pathlib.Path(r'E:\Current Cases\external-building-aerodynamics\examples\epw_to_stat\USA_MA_Boston-Logan.Intl.AP.725090_TMYx.2004-2018.epw')
epw = hc.HourlyContinuous()
epw.import_epw(epw_path)

statistics = hc.WeatherStatistics()
statistics.set_directions(np.arange(0, 360, 10))
statistics.set_speeds(np.arange(0.5, 16, 1))
statistics.set_hourly_continuous(epw)
sim.set_weather_statistics(statistics)

sim._create_hourly_continuous_windspeed()
    
'''
end = time.time()
print("Time taken to create speed matrix: {}".format(end - start))

## Validate the results by comparing the direction and speed in the file to the plot
# Assume just one comfort plot, i.e. use the last hc_speed
hour_no = int(np.random.uniform(low=1, high=8760, size=(1))[0])
print("Reference Speed: {}, Direction: {}".format(epw_speeds[hour_no], epw_directions[hour_no]))
f, ax = plt.subplots(1,1, sharex=True, sharey=True)
tpc = ax.tripcolor(points["X"], points["Y"], hc_speeds[:, hour_no])
ax.set_aspect('equal', 'box')
f.colorbar(tpc)
'''