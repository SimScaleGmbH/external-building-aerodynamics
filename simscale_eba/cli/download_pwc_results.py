import click

import simscale_eba.PWC_setup_results as pwc


@click.command("download-pwc-results")
@click.argument(
    'project',
    type=str
)
@click.argument(
    'simulation',
    type=str
)
@click.argument(
    'run',
    type=str
)
@click.argument(
    'resolution',
    type=float
)
@click.argument(
    'path',
    type=str
)
def download_pwc_results(project: str, simulation: str, run: str, resolution: float, path: str):
    sim = pwc.pedestrian_wind_comfort_results()

    sim.set_resolution(resolution)
    sim.get_pedestrian_wind_comfort(project, simulation, run, path=path)

    sim._create_dimensional_quantities()
    sim._create_dimensionless_quantities()

    sim.cluster_outputs()
