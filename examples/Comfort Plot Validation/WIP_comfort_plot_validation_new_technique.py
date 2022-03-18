# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 14:46:56 2021

@author: DarrenLynch
"""
import pathlib

import numpy as np

import simscale_eba.HourlyContinuous as hc
import simscale_eba.PedestrianWindComfort as pwc

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

project = "Outdoor Comfort Example"
simulation = "Pedestrian Wind Comfort 2"

results = pwc.pedestrian_wind_comfort_results()
results.get_pedestrian_wind_comfort(project=project,
                                    simulation=simulation,
                                    run="Run 1")

weather = hc.WeatherStatistics()
weather.set_wind_conditions(results.pedestrian_wind_comfort_setup.wind_conditions)
weather.set_speeds(np.arange(0.5, 20, 0.5).tolist())
weather.set_hourly_continuous(hourly_continuous)

results.set_weather_statistics(weather)

weather.to_stat()
comfort_dict = {
    "0": {"name": "Frequent Sitting",
          "description": None,
          "frequency": ["less", 2],
          "speed": 1.8
          },
    "1": {"name": "Occasional Sitting",
          "description": None,
          "frequency": ["less", 2],
          "speed": 3.6
          },
    "2": {"name": "Standing",
          "description": None,
          "frequency": ["less", 2],
          "speed": 5.3
          },
    "3": {"name": "Walking",
          "description": None,
          "frequency": ["less", 2],
          "speed": 7.6
          },
    "4": {"name": "Buisness Walking",
          "description": None,
          "frequency": ["greater", 2],
          "speed": 7.6
          },
}

comfort_criteria = pwc.comfort_criteria("CoL")
comfort_criteria.set_dict(comfort_dict)

results.set_comfort_criteria(comfort_criteria)

results.calculate_wind_comfort()
pwc.to_paraview(pathlib.Path("E:\Current Cases\SimScale Objects\simscale"), "comfort_map_UMag_CoL.result")
