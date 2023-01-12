import numpy as np
import pandas as pd

import pathlib
import csv

import simscale_eba.HourlyContinuous as hc
import simscale_eba.PWC_setup_results  as pwc
import simscale_eba.pwc_status as stat

def speed_to_json(path, speeds, directions):
    s = open(path + r'\speeds.csv', 'w')
    d = open(path + r'\directions.csv', 'w')
    
    speed_writer = csv.writer(s)
    direction_writer = csv.writer(d)
    
    speed_writer.writerow(speeds)
    direction_writer.writerow(directions)
    
    s.close()
    d.close()

def read_data(path):
    with open(path) as speeds:
        rows = csv.reader(speeds)
        for row in rows:
            if len(row)<1:
                break
            else:
                data = row
                
    return data

def arrays_to_hc_speeds(path):
    
    speeds = read_data(path.as_posix() + r'\speeds.csv')
    directions = read_data(path.as_posix() + r'\directions.csv')
    
    array = np.array([speeds, directions]).astype(float)
    
    df = pd.DataFrame(array.T, columns=['speed', 'direction'])
    
    epw = hc.HourlyContinuous()
    epw.hourly_continuous_df = df
    epw._original_df = df
    
    weather_stats = hc.WeatherStatistics()

    weather_stats.set_directions(np.arange(0, 360, 10))
    weather_stats.set_speeds(np.arange(0.5, 16, 1))
    weather_stats.set_hourly_continuous(epw)
    
    pwc_status = stat.simulation_status()
    pwc_status.set_result_directory(path)
    pwc_status.read_simulation_status()
    
    sim = pwc.pedestrian_wind_comfort_results(access_simscale=False)
    sim.set_weather_statistics(weather_stats)
    sim.status = pwc_status
    sim.result_directory = path
    
    names = sim._create_hourly_continuous_windspeed(output_file='csv')
    
    return names

speeds = np.random.uniform(low=0, high=20, size=(8760,))
directions = np.random.uniform(low=0, high=360, size=(8760,))

path = pathlib.Path("E:\Current Cases\Grasshopper Plugin")

speed_to_json(path.as_posix(), speeds, directions)
names = arrays_to_hc_speeds(path)