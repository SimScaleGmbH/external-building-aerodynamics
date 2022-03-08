import os

import click


def SetVars(api_url, api_key):
    '''
    Takes API key and URL, sets them to environment variables

    Parameters
    ----------
    api_url : str
        The SimScale API URL to call.
    api_key : str
        The SimScale API Key to use when calling, this is equivilent to
        the users password for the API, it should never be printed.

    '''
    try:
        os.environ["SIMSCALE_API_URL"] = str(api_url)
        os.environ['SIMSCALE_API_KEY'] = str(api_key)

        print("Your API key has ben set to the environment")
    except:
        raise Exception("Could not set environment variables")


@click.command("set-api-variables")
@click.argument(
    'api-url',
    type=str
)
@click.argument(
    'api-key',
    type=str
)
def set_variables(api_url, api_key):
    SetVars(api_url, api_key)
