import numpy as np
import pandas as pd


def csv_to_dimensionall_df(self, df, variables):
    '''
    Take a directional csv, return a dimensional field for each variable
    
    We reat in a csv file as df, we take the data we need based upon the
    list of variables, this data could be a single field, or a calulation
    combining several fields (such as speed from velocity components).

    Parameters
    ----------
    df : pd.DataFrame
        DESCRIPTION.
        
    variables : list[string]
        The variables you chose to return, current options are:
            
        - UMag
        - Ux
        - Uy
        - Uz
        - GEM
        - p
        - k_total
        - k_resolved
        - k_modeled

    Raises
    ------
    Exception
        If there exists a variable in the list that does not match expectation,
        throw exception.

    Returns
    -------
    output_df : pd.DataFrame
        A Dataframe, with number of points as number of rows, and a column 
        for each variable.

    '''
    output_df = pd.DataFrame(np.zeros((df.shape[0], len(variables))),
                             columns=variables)

    for variable in variables:
        result = None
        if variable == "UMag":
            result = wind_speed(df)

        elif variable == "Ux":
            result = velocity(df)[0]
        elif variable == "Uy":
            result = velocity(df)[1]
        elif variable == "Uz":
            result = velocity(df)[2]

        elif variable == "p":
            result = pressure(df)

        elif variable == "k_modeled":
            result = tke_modeled(df)
        elif variable == "k_resolved":
            result = tke_resolved(df)
        elif variable == "k_total":
            result = tke_total(df)

        elif variable == "GEM":
            result = tke_total(df)
        else:
            raise Exception("Cannot find field {}, field should be one of the following:"
                            "{}".format(variable, self.types.keys()))

        output_df[variable] = result

    return output_df


def csv_to_dimensionless_df(self, df, variables, direction):
    '''
    Take a directional csv, return a dimensionless field for each variable
    
    We read in a csv file as df, we take the data we need based upon the
    list of variables, this data could be a single field, or a calulation
    combining several fields (such as speed from velocity components).
    
    Making the fields dimensionless considers the type of field (speed,
    tke (turbulent kinetic energy) and pressure) and makes them dimensionless
    accordingly using the reference speed and meteorological corrector 
    from the ABL.

    Parameters
    ----------
    df : pd.DataFrame
        DESCRIPTION.
        
    variables : list[string]
        The variables you chose to return, current options are:
            
        - UMag
        - Ux
        - Uy
        - Uz
        - GEM
        - p
        - k_total
        - k_resolved
        - k_modeled

    Raises
    ------
    Exception
        If there exists a variable in the list that does not match expectation,
        throw exception.

    Returns
    -------
    output_df : pd.DataFrame
        A Dataframe, with number of points as number of rows, and a column 
        for each variable.

    '''
    df = df.copy()

    dimensional = csv_to_dimensionall_df(self, df, variables)

    output_df = pd.DataFrame(np.zeros((df.shape[0], len(variables))),
                             columns=variables)

    directional_dict = self.pedestrian_wind_comfort_setup.to_dict()

    meteorological_corrector = directional_dict[direction]["meteo_corrector"]

    # We should really retrieve density from the simulation setup. todo
    for variable in dimensional.columns:
        output_df[variable] = dimensional_to_dimensionless(dimensional[variable],
                                                           1.2,
                                                           10,
                                                           meteorological_corrector)

    return output_df


def dimensional_to_dimensionless(df,
                                 density,
                                 reference_speed,
                                 meteorological_corrector):
    '''
    Take a dimensional variable, return dimensionless based on type
    
    The type can be speed, pressure or tke, the variables are sorted into
    these types using the mapping:
        
                {
                "UMag": "speed",
                "Ux": "speed",
                "Uy": "speed",
                "Uz": "speed",
                "GEM": "speed",
                "p": "pressure",
                "k_total": "tke",
                "k_resolved": "tke",
                "k_modeled": "tke",
                }

    Parameters
    ----------
    df : pd.series
        A series of data, whic is one column of the dimensional DataFrame
        .
    density : float
        float of fluid density in kg/m3.
        
    reference_speed : float
        A float of reference speed at 10m, in m/s.
        
    meteorological_corrector : float
        A float of meteorological correction, from the ABL object.

    Raises
    ------
    Exception
        Throws an exception if the type is not speed, pressure or tke.

    Returns
    -------
    output_df : pd.series
        A series of the newly dimensionless data from dimensional data.

    '''

    variable_types = {
        "UMag": "speed",
        "Ux": "speed",
        "Uy": "speed",
        "Uz": "speed",
        "GEM": "speed",
        "p": "pressure",
        "k_total": "tke",
        "k_resolved": "tke",
        "k_modeled": "tke",
    }

    variable_type = variable_types[df.name]
    output_df = df.copy()

    if variable_type == "speed":
        output_df = df * (meteorological_corrector / reference_speed)
    elif variable_type == "pressure":
        output_df = df / (0.5 * density * (reference_speed / meteorological_corrector) ** 2)
    elif variable_type == "tke":
        output_df = df * ((meteorological_corrector / reference_speed) ** 2)
    else:
        raise Exception("Cannot find type {}, field should be one of the following:"
                        "{}".format(variable_type, ["speed", "pressure", "tke"]))

    return output_df


def wind_speed(df):
    '''
    Take a dataframe from .csv, return dimensional wind speed in m/s

    Parameters
    ----------
    df : pd.DataFrame
        A datafram of the csv read in.

    Returns
    -------
    UMag : np.array
        A numpy array of the wind speed in m/s.

    '''
    try:
        UMag = df["Velocity_n"].to_numpy()
    except:
        print("Cannot find field named Velocity_n, calculating from components...")
    else:
        u = df["Velocities_n:0"].to_numpy()
        v = df["Velocities_n:1"].to_numpy()
        w = df["Velocities_n:2"].to_numpy()

        UMag = np.sqrt(u ** 2 + v ** 2 + w ** 2).reshape(-1, 1)

    return UMag


def velocity(df):
    '''
    Take a dataframe from .csv, return dimensional velocity in m/s

    Parameters
    ----------
    df : pd.DataFrame
        A datafram of the csv read in.

    Returns
    -------
    u : np.array
        A numpy array of the velocity x component in m/s.
    v : np.array
        A numpy array of the velocity y component in m/s.
    w : np.array
        A numpy array of the velocity z component in m/s.

    '''
    u = df["Velocities_n:0"].to_numpy()
    v = df["Velocities_n:1"].to_numpy()
    w = df["Velocities_n:2"].to_numpy()

    return u, v, w


def tke_modeled(df):
    '''
    Take a dataframe from .csv, return dimensional modeled TKE in m^2/s^2

    Parameters
    ----------
    df : pd.DataFrame
        A datafram of the csv read in.

    Returns
    -------
    tke_modeled : np.array
        A numpy array of the modeled TKE in m^2/s^2.

    '''
    return df["urans_k_n"].to_numpy()


def tke_resolved(df):
    '''
    Take a dataframe from .csv, return dimensional resolved TKE in m^2/s^2

    Parameters
    ----------
    df : pd.DataFrame
        A datafram of the csv read in.

    Returns
    -------
    tke_resolved : np.array
        A numpy array of the resolved TKE in m^2/s^2.

    '''
    sigma = df["SigmaVelocity_n"].to_numpy()
    tke_resolved = (3 / 2) * sigma ** 2

    return tke_resolved


def tke_total(df):
    '''
    Take a dataframe from .csv, return dimensional total TKE in m^2/s^2

    Parameters
    ----------
    df : pd.DataFrame
        A datafram of the csv read in.

    Returns
    -------
    tke_total : np.array
        A numpy array of the total TKE in m^2/s^2.

    '''
    return tke_resolved(df) + tke_modeled(df)


def pressure(df):
    '''
    Take a dataframe from .csv, return dimensional pressure in Pa

    Parameters
    ----------
    df : pd.DataFrame
        A datafram of the csv read in.

    Returns
    -------
    pressure : np.array
        A numpy array of the pressure field in Pa.

    '''
    return df["Pressure_n"].to_numpy()


def gust_equivilent_mean(df, gust_factor=3.5):
    tke = tke_total(df)
    sigma = np.root((2 / 3) * tke)
    UMag = wind_speed(df)

    U_gust = UMag + 3.5 * sigma

    U_gem = U_gust / 1.85

    return U_gem
