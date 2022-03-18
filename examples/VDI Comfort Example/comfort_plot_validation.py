import pathlib

import numpy as np

import simscale_eba.HourlyContinuous as hc
import simscale_eba.PedestrianWindComfort as pwc
import simscale_eba.ResultProcessing as pp

# Inputs
project = "Outdoor Comfort Example"
simulation = "Pedestrian Wind Comfort 2"
run = "Run 1"
epw_path = pathlib.Path("E:/Current Cases/CFDtoHourly/Github/api-pollination-utci/assets/weather/CityofLondon2015.epw")

# Script
hourly_continuous = hc.HourlyContinuous()
hourly_continuous.import_epw(epw_path)

pwc_setup = pwc.pedestrian_wind_comfort_setup()
pwc_setup.get_project(project)
pwc_setup.get_simulation(simulation)
wind_conditions = pwc_setup.wind_conditions

weather = hc.WeatherStatistics()
weather.set_wind_conditions(wind_conditions)
weather.set_speeds(np.arange(0.5, 20, 0.5).tolist())
weather.set_hourly_continuous(hourly_continuous)

weather.to_stat()

results = pp.multi_directional_result()
results.set_weather_statistics(weather)
results.get_pedestrian_wind_comfort(project=project,
                                    simulation=simulation,
                                    run=run)

results.make_pedestrian_wind_comfort_non_dimensional()
results.make_local_weibul_parameters()

vdi_comfort_array = np.array([[6, 9, 12, 15],
                              [5.56, 8.33, 11.11, 13.89],
                              [5.13, 7.69, 10.25, 12.82],
                              [4.55, 6.82, 9.09, 11.37],
                              [3.83, 5.74, 7.66, 9.57],
                              [3.45, 5.17, 6.89, 8.62]])

vdi_comfort_labels = ['A', 'B', 'C', 'D']
vdi_frequency_bins = [0.01, 0.05, 0.2, 1, 5, 10]

i = 0
for frequency in vdi_frequency_bins:
    speeds = vdi_comfort_array[i]

    comfort_dict = {
        "0": {"name": vdi_comfort_labels[0],
              "description": None,
              "frequency": ["less", frequency],
              "speed": speeds[0]
              },
        "1": {"name": vdi_comfort_labels[1],
              "description": None,
              "frequency": ["less", frequency],
              "speed": speeds[1]
              },
        "2": {"name": vdi_comfort_labels[2],
              "description": None,
              "frequency": ["less", frequency],
              "speed": speeds[2]
              },
        "3": {"name": vdi_comfort_labels[3],
              "description": None,
              "frequency": ["less", frequency],
              "speed": speeds[3]
              }
    }

    comfort_criteria = pp.comfort_criteria("VDI {}".format(frequency))
    comfort_criteria.set_dict(comfort_dict)

    results.set_comfort_criteria(comfort_criteria)

    results.calculate_wind_comfort()
    test = results.weather_statistics.weibull_parameters

    comfort_path = pathlib.Path.cwd()
    pp.to_paraview(comfort_path, "comfort_map_VDI {}.result".format(frequency))

    i += 1
