import pathlib

import numpy as np

import simscale_eba.HourlyContinuous as hc

epw = hc.HourlyContinuous()

# Put any path here
path = r'E:\Current Cases\external-building-aerodynamics\examples\epw_to_stat\USA_MA_Boston-Logan.Intl.AP.725090_TMYx.2004-2018.epw'
epw.import_epw(pathlib.Path(path))

#Set aperiod, summer only, between 7am and 6pm
period = hc.WeatherPeriod()
period.set_name('summer')
period.set_start_datetime(7, 1, 7)
period.set_end_datetime(18, 30, 9)

epw.set_period(period)

#Create statistics for the stat file, use 36 wind directions, set the 
#speed bins from 0.5m/s in 1m/s increments
weather_stats = hc.WeatherStatistics()
weather_stats.set_directions(np.arange(0, 360, 10))
weather_stats.set_speeds(np.arange(0.5, 16, 1))
weather_stats.set_hourly_continuous(epw)

#Export for SimScale
weather_stats.to_stat()

#Plot the mathmatical distribution for each direction
weather_stats.plot_cumulative_distributions()