import pathlib
import sys

import numpy as np

sys.path.append('E:\Current Cases\SimScale Objects\simscale')

import simscale_eba.HourlyContinuous as hc

historic = hc.HourlyContinuous()

# Put any path here
path = r'E:\Current Cases\SimScale Objects\weather_files\climate-source-file_thermalComfort.xlsx'
historic.import_city_of_london_historic(pathlib.Path(path))

weather_stats = hc.WeatherStatistics()
weather_stats.set_directions(np.arange(0, 360, 10))
weather_stats.set_speeds(np.arange(0.5, 16, 1))
weather_stats.set_hourly_continuous(historic)

# weather_stats.plot_probability_distributions()
weather_stats.get_highest_speeds(periods='quarter')
weather_stats.get_gumbel_extreeme_speed(in_years=100)
weather_stats.plot_gumbel_correlation()

print("Maximum speed in return period is {}".format(weather_stats.extreeme_speed))
