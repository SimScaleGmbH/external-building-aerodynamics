import click

import numpy as np
import pandas as pd

import pathlib
import csv

import simscale_eba.HourlyContinuous as hc
import simscale_eba.PWC_setup_results as pwc
import simscale_eba.pwc_status as stat

@click.command("create-speed-matrix")
@click.argument(
    'path',
    type=str
)
def create_speed_matrix(path: str):
    
    def read_data(path):
        with open(path) as speeds:
            rows = csv.reader(speeds)
            for row in rows:
                if len(row)<1:
                    break
                else:
                    data = row
                    
        return data
    path = pathlib.Path(path)
    
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
    
    click.echo(names)