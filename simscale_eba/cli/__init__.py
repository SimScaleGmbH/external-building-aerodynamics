import click

from .read_direction import return_list
from .cast_ordinate import cast
from .set_env_variables import set_variables
from .download_pwc_results import download_pwc_results
from .cast_data import cast_speed, cast_ordinate
from .create_speed_matrix import create_speed_matrix

@click.group()
def main():
    pass


main.add_command(return_list)
main.add_command(cast)
main.add_command(set_variables)
main.add_command(download_pwc_results)
main.add_command(cast_speed)
main.add_command(cast_ordinate)
main.add_command(create_speed_matrix)