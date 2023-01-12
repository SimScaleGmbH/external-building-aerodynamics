import pathlib

import simscale_eba.HourlyContinuous as hc
import simscale_eba.PWC_setup_results as pwc
import simscale_eba.pwc_status as stat

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
run = "Run 1"

results = pwc.pedestrian_wind_comfort_results()
results.get_pedestrian_wind_comfort(project=project,
                                    simulation=simulation,
                                    run=run)

results._create_dimensionless_quantities()
results._create_point_file()

status = stat.simulation_status()
status.set_simulation(project, simulation, run)
status.set_result_directory("E:\Current Cases\SimScale Objects\examples\PWC Downloader")
status.read_simulation_status()

dimensional_results = pwc.dimensionaliser(status)
points = dimensional_results.return_points()
speed = dimensional_results.return_dimensional_speed(5, 5)
