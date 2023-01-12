import pathlib

import click
import pandas as pd

import simscale_eba.PWC_setup_results as pwc
import simscale_eba.pwc_status as stat


@click.command("cast-speed")
@click.argument(
    'path',
    type=str
)
@click.argument(
    'direction',
    type=float
)
@click.argument(
    'reference_speed',
    type=float
)
def cast_speed(path: str, direction: str, reference_speed: str):
    path = pathlib.Path(path)

    pwc_status = stat.simulation_status()
    pwc_status.set_result_directory(path)
    pwc_status.read_simulation_status()

    field_paths = pwc_status.field_paths["dimensionless_UMag"]

    speeds = []

    for key in field_paths.keys():
        field_path = pathlib.Path(field_paths[key])

        rounded_direction = pwc.round_direction(field_path, direction)

        field = pd.read_feather(field_path)[str(rounded_direction)]
        speed = (field * reference_speed).values.T.tolist()

        speeds.append(speed)

    click.echo(speeds)


@click.command("cast-ordinate")
@click.argument(
    'path',
    type=str
)
@click.argument(
    'ordinate',
    type=str
)
def cast_ordinate(path: str, ordinate: str):
    path = pathlib.Path(path)

    pwc_status = stat.simulation_status()
    pwc_status.set_result_directory(path)
    pwc_status.read_simulation_status()

    points_paths = pwc_status.points_path

    ordinate_list = []

    for key in points_paths.keys():
        points_path = pathlib.Path(points_paths[key])

        points = pd.read_feather(points_path)
        points = points.set_index("index", drop=True)

        ordinates = points[ordinate].values.T.tolist()

        ordinate_list.append(ordinates)

    click.echo(ordinate_list)


'''
path = r"E:\Current Cases\WSP\working_dir\Lower"
cast_speed(path, str(45), str(10))
paths = cast_ordinate(path, "X")
'''
