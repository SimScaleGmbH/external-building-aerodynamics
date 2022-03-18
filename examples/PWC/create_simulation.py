import pathlib

import simscale_eba.ExternalBuildingAssessment as eb
import simscale_eba.TestConditions as tc
import simscale_eba.WindTunnel as wt

comfort_study = eb.PedestrianComfort()

name = "Outdoor Comfort Example"
description = "A pedestrian comfort sim created via the API"
comfort_study.create_new_project(name, description)

geometry_path = pathlib.Path.cwd() / "buildings.stl"
geometry_name = "Buildings"
comfort_study.upload_geometry(geometry_name, geometry_path)

roi = wt.RegionOfInterest()
roi.set_centre([118.5, -86.5])
roi.set_height(0)
roi.set_radius(100)
roi.set_windtunnel_size()

wind_conditions = tc.WindData()

wind_conditions.set_atmospheric_boundary_layers(method_dict={
    "u": "LOGLAW",
    "tke": "YGCJ",
    "omega": "YGCJ"
})

comfort_study.set_region_of_interest(roi)
comfort_study.set_wind_conditions(wind_conditions)

comfort_study.create_wind_tunnel()
comfort_study.upload_abl_profiles()

grid_path = pathlib.Path.cwd() / "ladybug_points"
comfort_study.import_ladybug_grid(grid_path, "Comfort plot")

sim_name = "Example"
comfort_study.create_simulation(sim_name)

comfort_study.set_run_ids(2)
comfort_study.run_all_directions()
