import pathlib

import numpy as np

import simscale_eba.HourlyContinuous as hc

epw = hc.HourlyContinuous()

# Put any path here
path = r'E:\Current Cases\SimScale Objects\examples\epw_to_stat\USA_MA_Boston-Logan.Intl.AP.725090_TMYx.2004-2018.epw'
epw.import_epw(pathlib.Path(path))

weather_stats = hc.WeatherStatistics()
weather_stats.set_directions(np.arange(0, 360, 10))
weather_stats.set_speeds(np.arange(0.5, 16, 1))
weather_stats.set_hourly_continuous(epw)

weather_stats.to_stat()
weather_stats.plot_cumulative_distributions()
