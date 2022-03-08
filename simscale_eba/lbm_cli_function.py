import json
import pathlib

import simscale_eba.ExternalBuildingAssessment as eb
import simscale_eba.TestConditions as tc
import simscale_eba.WindTunnel as wt


def json_to_eba(path):
    with open(path) as json_file:
        data = json.load(json_file)

    project_name = data["project"]["name"]
    project_description = data["project"]["discription"]

    simulation_name = (data["project"]
    ["simulation"]
    ["name"]
    )

    run_id = (data["project"]
    ["simulation"]
    ["run"]
    )

    geometry_name = (data["project"]
    ["simulation"]
    ["setup"]
    ["geometry"]
    ["name"]
    )

    geometry_path = pathlib.Path(
        data["project"]
        ["simulation"]
        ["setup"]
        ["geometry"]
        ["path"]
    )

    roi_centre = (data["project"]
    ["simulation"]
    ["setup"]
    ["roi"]
    ["centre"]
    )

    roi_height = (data["project"]
    ["simulation"]
    ["setup"]
    ["roi"]
    ["ground height"]
    )

    roi_radius = (data["project"]
    ["simulation"]
    ["setup"]
    ["roi"]
    ["radius"]
    )

    direction = (data["project"]
    ["simulation"]
    ["setup"]
    ["wind conditions"]
    ["direction"]
    )

    roughness = (data["project"]
    ["simulation"]
    ["setup"]
    ["wind conditions"]
    ["roughness"]
    )

    reference_speed = (data["project"]
    ["simulation"]
    ["setup"]
    ["wind conditions"]
    ["reference speed"]
    )

    reference_height = (data["project"]
    ["simulation"]
    ["setup"]
    ["wind conditions"]
    ["reference height"]
    )

    grid_name = (data["project"]
    ["simulation"]
    ["setup"]
    ["comfort plot"]
    ["name"]
    )

    grid_path = pathlib.Path(
        data["project"]
        ["simulation"]
        ["setup"]
        ["comfort plot"]
        ["path"]
    )

    comfort_study = eb.PedestrianComfort()

    comfort_study.create_new_project(project_name, project_description)

    comfort_study.upload_geometry(geometry_name, geometry_path)

    roi = wt.RegionOfInterest()
    roi.set_centre(roi_centre)
    roi.set_height(roi_height)
    roi.set_radius(roi_radius)
    roi.set_windtunnel_size()

    wind_conditions = tc.WindData()

    wind_conditions.set_atmospheric_boundary_layers(directions=direction,
                                                    surface_roughness_list=roughness,
                                                    reference_speeds=reference_speed,
                                                    reference_heights=reference_height)

    comfort_study.set_region_of_interest(roi)
    comfort_study.set_wind_conditions(wind_conditions)

    comfort_study.create_wind_tunnel()
    comfort_study.upload_abl_profiles()

    comfort_study.import_ladybug_grid(grid_path, grid_name)

    comfort_study.create_simulation(simulation_name)

    comfort_study.set_run_ids(run_id)
    comfort_study.run_all_directions()
