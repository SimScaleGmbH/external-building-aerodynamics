import click

import numpy as np
import pandas as pd

import pathlib

import simscale_eba.HourlyContinuous as hc
import simscale_eba.PedestrianWindComfort as pwc
import simscale_eba.pwc_status as stat

@click.command("create-speed-matrix")
@click.argument(
    'path',
    type=str
)
@click.argument(
    'speeds',
    type=list
)
@click.argument(
    'directions',
    type=list
)
def arrays_to_hc_speeds(path: str, speeds: str, directions: str):
    path = pathlib.Path(path)
    
    df = pd.DataFrame(np.array([speeds, directions]).T, columns=['speed', 'direction'])
    
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