import pathlib

import click
import pandas as pd


@click.command("cast-ordinate")
@click.argument(
    'path',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True)
)
@click.argument(
    'ordinate',
    type=str
)
def cast(path, ordinate):
    path = pathlib.Path(path)

    df = pd.read_csv(path, usecols=[str(ordinate)])

    ordinate = df.values.T.tolist()[0]
    click.echo(ordinate)


'''
path = "E:\Current Cases\City of LondonThermal Comfort\Results\\reduced_points.csv"
z = cast(path, 'Z')
'''
