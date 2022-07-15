import numpy as np
import pandas as pd

import pathlib

import simscale_eba.HourlyContinuous as hc
import simscale_eba.PedestrianWindComfort as pwc
import simscale_eba.pwc_status as stat

def arrays_to_hc_speeds(path, speeds, directions):
    
    df = pd.DataFrame(np.array([speeds, directions]).T, columns=['speed', 'direction'])
    
    epw = hc.HourlyContinuous()
    epw.hourly_continuous_df = df
    
    weather_stats = hc.WeatherStatistics()

    weather_stats.set_directions(np.arange(0, 360, 10))
    weather_stats.set_speeds(np.arange(0.5, 16, 1))
    weather_stats.set_hourly_continuous(epw)
    
    #weather_stats.plot_windrose()
    
    pwc_status = stat.simulation_status()
    pwc_status.set_result_directory(path)
    pwc_status.read_simulation_status()
    
    sim = pwc.pedestrian_wind_comfort_results()
    sim.set_weather_statistics(weather_stats)
    sim.status = pwc_status
    
    #sim._create_hourly_continuous_windspeed()
    
    return weather_stats

speeds = np.random.uniform(low=0, high=20, size=(8760,))
directions = np.random.uniform(low=0, high=360, size=(8760,))

path = pathlib.Path("E:\Current Cases\Grasshopper Plugin")

df = arrays_to_hc_speeds(path, speeds, directions)