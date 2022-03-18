import pathlib

import numpy as np

import simscale_eba.HourlyContinuous as hc
import simscale_eba.ResultProcessing as pp
import simscale_eba.TestConditions as tc

wind_conditions = tc.WindData()

wind_conditions.set_atmospheric_boundary_layers()

epw_path = pathlib.Path("E:/Current Cases/CFDtoHourly/Github/api-pollination-utci/assets/weather/CityofLondon2015.epw")
# epw_path = pathlib.Path.cwd() / "USA_MA_Boston-Logan.Intl.AP.725090_TMYx.2004-2018.epw"
hourly_continuous = hc.HourlyContinuous()
hourly_continuous.import_epw(epw_path)

weather = hc.WeatherStatistics()
weather.set_wind_conditions(wind_conditions)
weather.set_speeds(np.arange(0.5, 20, 0.5).tolist())
weather.set_hourly_continuous(hourly_continuous)

weather.to_stat()

results = pp.multi_directional_result()
results.set_weather_statistics(weather)
results.get_pedestrian_wind_comfort(project="Outdoor Comfort Example",
                                    simulation="Pedestrian Wind Comfort 2",
                                    run="Run 1")

results.make_pedestrian_wind_comfort_non_dimensional()
results.make_local_weibul_parameters()
'''
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

comfort_criteria = pp.comfort_criteria("CoL")
comfort_criteria.set_dict(comfort_dict)

results.set_comfort_criteria(comfort_criteria)

results.calculate_wind_comfort()
test = results.weather_statistics.weibull_parameters

comfort_path = pathlib.Path.cwd()
pp.to_paraview(comfort_path, "comfort_map_CoL.result")
pp.to_paraview(comfort_path, "gamma.result")
'''
print(results.weather_statistics.weibull_parameters)
