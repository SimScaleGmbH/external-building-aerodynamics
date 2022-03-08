import warnings

import numpy as np
import pint as pt

warnings.filterwarnings("ignore", category=pt.errors.UnitStrippedWarning)


def u_log_law(unit,
              reference_speed,
              reference_height,
              height,
              aerodynamic_roughness,
              return_without_units=True,
              debug=False):
    '''
    Take reference values, return wind speeds at given height(s).

    Parameters
    ----------
    reference_speed : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The reference speed taken at the reference height, 
        usually taken to be 10m in SimScale. If no dimenson is supplied
        we assume meters per second.
        
    reference_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The height in which we measure the reference speed,
        usually taken to be 10m/s in SimScale. If no dimenson is supplied
        we assume meters.
        
    height : float or np.array().astype(float64) or 
    pint.quantity.build_quantity_class.<locals>.Quantity
        The heights in which to return the velocity results at, this can
        be an array, or a single value. If no dimenson is supplied
        we assume meters.
        
    aerodynamic_roughness : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The aerodynamic roughness of the AbL profile. 
        
    return_without_units : bool.
        True returns the numpy array as a numpy array without units assuming
        the unit is default SI, this makes it harder to convert if using other
        units.
        
    debug : bool, optional
        Returns more detail in the command line, more functionality to
        be added later. The default is False.
        
    Returns
    -------
    u : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        the velocity at specified height or heights.

    '''
    # return expected dimensional unit types
    distance = 1 * unit.meter
    distance_type = type(distance)

    speed = 1 * unit.meter / unit.second
    speed_type = type(speed)

    # Check if the inputs have units, if not, assume the units are
    # default SI units, i.e. meters for distance, meters/second for speed etc
    if not isinstance(reference_speed, speed_type):
        reference_speed = reference_speed * speed

    if not isinstance(reference_height, distance_type):
        reference_height = reference_height * distance

    if not isinstance(aerodynamic_roughness, distance_type):
        aerodynamic_roughness = aerodynamic_roughness * distance

    if not isinstance(height, distance_type):
        height = height * distance

    if debug:
        print(reference_speed)
        print(reference_height)
        print(aerodynamic_roughness)
        print(height)

    u = reference_speed * (
        (np.log(
            (height + aerodynamic_roughness) / aerodynamic_roughness)
         / np.log(
                    (reference_height + aerodynamic_roughness) / aerodynamic_roughness)
         ))

    # If a raw numpy array is needed, we can simply ask for the same array
    # stripped of its units
    if return_without_units:
        u = np.array(u)

    return u


def u_eurocode(unit,
               reference_speed,
               reference_height,
               height,
               aerodynamic_roughness,
               return_without_units=True,
               debug=False):
    '''
    Take reference values, return wind speeds at given height(s).

    Parameters
    ----------
    reference_speed : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The reference speed taken at the reference height, 
        usually taken to be 10m in SimScale. If no dimenson is supplied
        we assume meters per second.
        
    reference_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The height in which we measure the reference speed,
        usually taken to be 10m/s in SimScale. If no dimenson is supplied
        we assume meters.
        
    height : float or np.array().astype(float64) or 
    pint.quantity.build_quantity_class.<locals>.Quantity
        The heights in which to return the velocity results at, this can
        be an array, or a single value. If no dimenson is supplied
        we assume meters.
        
    aerodynamic_roughness : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The aerodynamic roughness of the AbL profile. 
        
    return_without_units : bool.
        True returns the numpy array as a numpy array without units assuming
        the unit is default SI, this makes it harder to convert if using other
        units.
        
    debug : bool, optional
        Returns more detail in the command line, more functionality to
        be added later. The default is False.
        
    Returns
    -------
    u : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        the velocity at specified height or heights.

    '''
    # return expected dimensional unit types
    distance = 1 * unit.meter
    distance_type = type(distance)

    speed = 1 * unit.meter / unit.second
    speed_type = type(speed)

    # Check if the inputs have units, if not, assume the units are
    # default SI units, i.e. meters for distance, meters/second for speed etc
    if not isinstance(reference_speed, speed_type):
        reference_speed = reference_speed * speed

    if not isinstance(reference_height, distance_type):
        reference_height = reference_height * distance

    if not isinstance(aerodynamic_roughness, distance_type):
        aerodynamic_roughness = aerodynamic_roughness * distance

    if not isinstance(height, distance_type):
        height = height * distance

    if debug:
        print(reference_speed)
        print(reference_height)
        print(aerodynamic_roughness)
        print(height)

    krz0 = 0.19 * (aerodynamic_roughness / 0.05) ** 0.07
    cz = krz0 * np.log(height / aerodynamic_roughness)
    cr = krz0 * np.log(reference_height / aerodynamic_roughness)

    u = (cz / cr) * reference_speed
    zmin = get_eurocode_minimum_height(unit, aerodynamic_roughness)

    cmin = krz0 * np.log(zmin / aerodynamic_roughness)
    if u.shape != ():
        u[height < zmin] = (cmin / cr) * reference_speed
    else:
        if height < zmin:
            (cmin / cr) * reference_speed

    # If a raw numpy array is needed, we can simply ask for the same array
    # stripped of its units
    if return_without_units:
        u = np.array(u)

    return u


def u_power_law(unit,
                reference_speed,
                reference_height,
                height,
                alpha,
                return_without_units=True,
                debug=False):
    '''
    Take reference values, return wind speeds at given height(s).

    Parameters
    ----------
    reference_speed : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The reference speed taken at the reference height, 
        usually taken to be 10m in SimScale. If no dimenson is supplied
        we assume meters per second.
        
    reference_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The height in which we measure the reference speed,
        usually taken to be 10m/s in SimScale. If no dimenson is supplied
        we assume meters.
        
    height : float or np.array().astype(float64) or 
    pint.quantity.build_quantity_class.<locals>.Quantity
        The heights in which to return the velocity results at, this can
        be an array, or a single value. If no dimenson is supplied
        we assume meters.
        
    alpha : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The exponent of the Power Law
        
    return_without_units : bool.
        True returns the numpy array as a numpy array without units assuming
        the unit is default SI, this makes it harder to convert if using other
        units.
        
    debug : bool, optional
        Returns more detail in the command line, more functionality to
        be added later. The default is False.
        
    Returns
    -------
    u : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        The velocity at specified height or heights.

    '''
    # return expected dimensional unit types
    distance = 1 * unit.meter
    distance_type = type(distance)

    speed = 1 * unit.meter / unit.second
    speed_type = type(speed)

    dimensionless = 1 * unit.meter / unit.meter
    dimensionless_type = type(dimensionless)

    # Check if the inputs have units, if not, assume the units are
    # default SI units, i.e. meters for distance, meters/second for speed etc
    if not isinstance(reference_speed, speed_type):
        reference_speed = reference_speed * speed

    if not isinstance(reference_height, distance_type):
        reference_height = reference_height * distance

    if not isinstance(alpha, dimensionless_type):
        alpha = alpha * dimensionless

    if not isinstance(height, distance_type):
        height = height * distance

    if debug:
        print(reference_speed)
        print(reference_height)
        print(alpha)
        print(height)

    u = reference_speed * (height / reference_height) ** alpha

    # If a raw numpy array is needed, we can simply ask for the same array
    # stripped of its units
    if return_without_units:
        u = np.array(u)

    return u


def calulate_u_star(unit,
                    reference_speed,
                    reference_height,
                    aerodynamic_roughness,
                    k=0.41,
                    return_without_units=True,
                    debug=False):
    '''
    take reference values, return the friction velocity

    Parameters
    ----------
    reference_speed : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The reference speed taken at the reference height, 
        usually taken to be 10m in SimScale. If no dimenson is supplied
        we assume meters per second.
        
    reference_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The height in which we measure the reference speed,
        usually taken to be 10m/s in SimScale. If no dimenson is supplied
        we assume meters.
        
    aerodynamic_roughness : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The aerodynamic roughness of the AbL profile. 
        
    k : float, optional
        The von karman constant. The default is 0.41.
        
    return_without_units : bool, optional
    True returns the numpy array as a numpy array without units assuming
        the unit is default SI, this makes it harder to convert if using other
        units. The default is True.
        
    debug : bool, optional
        Returns more detail in the command line, more functionality to
        be added later. The default is False.

    Returns
    -------
    u_star : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The friction velocity.

    '''
    # return expected dimensional unit types
    distance = 1 * unit.meter
    distance_type = type(distance)

    speed = 1 * unit.meter / unit.second
    speed_type = type(speed)

    # Check if the inputs have units, if not, assume the units are
    # default SI units, i.e. meters for distance, meters/second for speed etc
    if not isinstance(reference_speed, speed_type):
        reference_speed = reference_speed * speed

    if not isinstance(reference_height, distance_type):
        reference_height = reference_height * distance

    if not isinstance(aerodynamic_roughness, distance_type):
        aerodynamic_roughness = aerodynamic_roughness * distance

    if debug:
        print(reference_speed)
        print(reference_height)
        print(aerodynamic_roughness)

    u_star = (reference_speed * k) / (np.log((reference_height + aerodynamic_roughness) / aerodynamic_roughness))

    if return_without_units:
        u_star = np.array(u_star)
    return u_star


def i_eurocode(unit,
               height,
               aerodynamic_roughness,
               return_without_units=True,
               debug=False):
    '''
    Take reference values, return wind speeds at given height(s).

    Parameters
    ----------
        
    height : float or np.array().astype(float64) or 
    pint.quantity.build_quantity_class.<locals>.Quantity
        The heights in which to return the velocity results at, this can
        be an array, or a single value. If no dimenson is supplied
        we assume meters.
        
    aerodynamic_roughness : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The aerodynamic roughness of the AbL profile. 
        
    return_without_units : bool.
        True returns the numpy array as a numpy array without units assuming
        the unit is default SI, this makes it harder to convert if using other
        units.
        
    debug : bool, optional
        Returns more detail in the command line, more functionality to
        be added later. The default is False.
        
    Returns
    -------
    i : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        The intensity at specified height or heights.

    '''
    # return expected dimensional unit types
    distance = 1 * unit.meter
    distance_type = type(distance)

    # Check if the inputs have units, if not, assume the units are
    # default SI units, i.e. meters for distance, meters/second for speed etc
    if not isinstance(aerodynamic_roughness, distance_type):
        aerodynamic_roughness = aerodynamic_roughness * distance

    if not isinstance(height, distance_type):
        height = height * distance

    if debug:
        print(aerodynamic_roughness)
        print(height)

    i = 1 / np.log(height / aerodynamic_roughness)

    zmin = get_eurocode_minimum_height(unit, aerodynamic_roughness)
    i[height < zmin] = 1 / np.log(zmin / aerodynamic_roughness)

    # If a raw numpy array is needed, we can simply ask for the same array
    # stripped of its units
    if return_without_units:
        i = np.array(i)

    return i


def tke_derived(unit,
                u,
                intensity,
                return_without_units=True,
                debug=False):
    '''
    Take reference values, return TKE at given height(s).

    Parameters
    ----------
    u : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        The height dependent streamwise wind speed.
        
    intensity : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        The height dependent turbulent intensity.
        
    return_without_units : bool.
        True returns the numpy array as a numpy array without units assuming
        the unit is default SI, this makes it harder to convert if using other
        units.
        
    debug : bool, optional
        Returns more detail in the command line, more functionality to
        be added later. The default is False.
        
    Returns
    -------
    tke : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        The turbulent kinetic energy as a function of height.

    '''
    # check there is data
    if u.size == 0:
        raise OrderError("set_tke", "Error: define the wind speed profile first using set_streamwise_speed(method)")
    if intensity.size == 0:
        raise OrderError("set_tke", "Error: define the intensity profile first using set_streamwise_speed(method)")
    # return expected dimensional unit types
    speed = 1 * unit.meter / unit.second
    speed_type = type(speed)

    dimensionless = 1 * unit.meter / unit.meter
    dimensionless_type = type(dimensionless)

    # Check if the inputs have units, if not, assume the units are
    # default SI units, i.e. meters for distance, meters/second for speed etc
    if not isinstance(u, speed_type):
        u = u * speed

    if not isinstance(intensity, dimensionless_type):
        intensity = intensity * dimensionless_type

    if debug:
        print(u)
        print(intensity)

    tke = (3 / 2) * (u * intensity) ** 2

    # If a raw numpy array is needed, we can simply ask for the same array
    # stripped of its units
    if return_without_units:
        tke = np.array(tke)

    return tke


def tke_uniform(unit,
                height,
                tke,
                return_without_units=True,
                debug=False):
    '''
    Take reference values, return TKE at given height(s).

    Parameters
    ----------
    height : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        The heights in which to return the velocity results at, this can
        be an array, or a single value. If no dimenson is supplied
        we assume meters.
        
    tke : float or pint.quantity.build_quantity_class.<locals>.Quantity
        A value of TKE for the uniform velocity profile.
    
    return_without_units : bool, optional
        True returns the numpy array as a numpy array without units assuming
        the unit is default SI, this makes it harder to convert if using other
        units.. The default is True.
        
    debug : bool, optional
        Returns more detail in the command line, more functionality to
        be added later. The default is False.. The default is False.

    Returns
    -------
    tke : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        The turbulent kinetic energy as a function of height.

    '''
    # return expected dimensional unit types
    distance = 1 * unit.meter
    distance_type = type(distance)

    energy = 1 * unit.meter ** 2 / unit.second ** 2
    tke_type = type(energy)

    if not isinstance(height, distance_type):
        height = height * distance

    if not isinstance(tke, tke_type):
        tke = tke * tke_type

    if debug:
        print(height)

    ones = np.ones(len(height))
    tke = (ones * tke)

    # If a raw numpy array is needed, we can simply ask for the same array
    # stripped of its units
    if return_without_units:
        tke = np.array(tke)

    return tke


def tke_YGCJ(unit,
             reference_speed,
             reference_height,
             height,
             aerodynamic_roughness,
             c1, c2,
             return_without_units=True,
             debug=False):
    '''
    Take reference values, return TKE at given heights.


    Expression generalisations to allow height
                variation for turbulence quantities (tag:YGCJ):
                Yang, Y., Gu, M., Chen, S., & Jin, X. (2009).
                New inflow boundary conditions for modelling the neutral 
                equilibrium atmospheric boundary layer in computational 
                wind engineering. J. of Wind Engineering and Industrial 
                Aerodynamics, 97(2), 88-95.
                DOI:10.1016/j.jweia.2008.12.001

    Parameters
    ----------
    reference_speed : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The reference speed taken at the reference height, 
        usually taken to be 10m in SimScale. If no dimenson is supplied
        we assume meters per second.
        
    reference_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The height in which we measure the reference speed,
        usually taken to be 10m/s in SimScale. If no dimenson is supplied
        we assume meters.
        
    height : float or np.array().astype(float64) or 
    pint.quantity.build_quantity_class.<locals>.Quantity
        The heights in which to return the velocity results at, this can
        be an array, or a single value. If no dimenson is supplied
        we assume meters.
        
    aerodynamic_roughness : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The aerodynamic roughness of the AbL profile. 
        
    c1 : float
        fitting coefficient 1
        
    c2 : float
        fitting coefficient 2
        
    return_without_units : bool.
        True returns the numpy array as a numpy array without units assuming
        the unit is default SI, this makes it harder to convert if using other
        units.
        
    debug : bool, optional
        Returns more detail in the command line, more functionality to
        be added later. The default is False.
        
    Returns
    -------
    u : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        the velocity at specified height or heights.

    '''
    # return expected dimensional unit types
    distance = 1 * unit.meter
    distance_type = type(distance)

    speed = 1 * unit.meter / unit.second
    speed_type = type(speed)

    # Check if the inputs have units, if not, assume the units are
    # default SI units, i.e. meters for distance, meters/second for speed etc
    if not isinstance(reference_speed, speed_type):
        reference_speed = reference_speed * speed

    if not isinstance(reference_height, distance_type):
        reference_height = reference_height * distance

    if not isinstance(aerodynamic_roughness, distance_type):
        aerodynamic_roughness = aerodynamic_roughness * distance

    if not isinstance(height, distance_type):
        height = height * distance

    if debug:
        print(reference_speed)
        print(reference_height)
        print(aerodynamic_roughness)
        print(height)

    u_star = calulate_u_star(unit,
                             reference_speed,
                             reference_height,
                             aerodynamic_roughness,
                             return_without_units=False)
    cmu = 0.09

    tke = (u_star ** 2 / cmu ** 0.5) * (
                (c1 * np.log((height + aerodynamic_roughness) / aerodynamic_roughness)) + c2) ** 0.5

    # If a raw numpy array is needed, we can simply ask for the same array
    # stripped of its units
    if return_without_units:
        tke = np.array(tke)

    return tke


def omega_YGCJ(
        unit,
        reference_speed,
        reference_height,
        height,
        aerodynamic_roughness,
        return_without_units=True,
        debug=False

):
    '''
    Take reference values, return TKE at given heights.


    Expression generalisations to allow height
                variation for turbulence quantities (tag:YGCJ):
                Yang, Y., Gu, M., Chen, S., & Jin, X. (2009).
                New inflow boundary conditions for modelling the neutral 
                equilibrium atmospheric boundary layer in computational 
                wind engineering. J. of Wind Engineering and Industrial 
                Aerodynamics, 97(2), 88-95.
                DOI:10.1016/j.jweia.2008.12.001

    Parameters
    ----------
    reference_speed : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The reference speed taken at the reference height, 
        usually taken to be 10m in SimScale. If no dimenson is supplied
        we assume meters per second.
        
    reference_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The height in which we measure the reference speed,
        usually taken to be 10m/s in SimScale. If no dimenson is supplied
        we assume meters.
        
    height : float or np.array().astype(float64) or 
    pint.quantity.build_quantity_class.<locals>.Quantity
        The heights in which to return the velocity results at, this can
        be an array, or a single value. If no dimenson is supplied
        we assume meters.
        
    aerodynamic_roughness : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The aerodynamic roughness of the AbL profile. 
        
    return_without_units : bool.
        True returns the numpy array as a numpy array without units assuming
        the unit is default SI, this makes it harder to convert if using other
        units.
        
    debug : bool, optional
        Returns more detail in the command line, more functionality to
        be added later. The default is False.
        
    Returns
    -------
    u : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        the velocity at specified height or heights.

    '''
    # return expected dimensional unit types
    distance = 1 * unit.meter
    distance_type = type(distance)

    speed = 1 * unit.meter / unit.second
    speed_type = type(speed)

    # Check if the inputs have units, if not, assume the units are
    # default SI units, i.e. meters for distance, meters/second for speed etc
    if not isinstance(reference_speed, speed_type):
        reference_speed = reference_speed * speed

    if not isinstance(reference_height, distance_type):
        reference_height = reference_height * distance

    if not isinstance(aerodynamic_roughness, distance_type):
        aerodynamic_roughness = aerodynamic_roughness * distance

    if not isinstance(height, distance_type):
        height = height * distance

    if debug:
        print(reference_speed)
        print(reference_height)
        print(aerodynamic_roughness)
        print(height)

    u_star = calulate_u_star(unit,
                             reference_speed,
                             reference_height,
                             aerodynamic_roughness,
                             return_without_units=False)
    cmu = 0.09  # model coef
    k = 0.41  # von karman constant

    omega = ((u_star / (k * cmu ** 0.5))
             * (1 / (height + aerodynamic_roughness)))

    # If a raw numpy array is needed, we can simply ask for the same array
    # stripped of its units
    if return_without_units:
        omega = np.array(omega)

    return omega


def omega_AIJ(unit,
              u,
              tke,
              return_without_units=True,
              debug=False):
    '''
    Take reference values, return TKE at given height(s).

    Parameters
    ----------
    u : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        The height dependent streamwise wind speed.
        
    tke : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        The height dependent turbulent kinetic energy.
        
    return_without_units : bool.
        True returns the numpy array as a numpy array without units assuming
        the unit is default SI, this makes it harder to convert if using other
        units.
        
    debug : bool, optional
        Returns more detail in the command line, more functionality to
        be added later. The default is False.
        
    Returns
    -------
    omega : np.array().astype(float64) or pint.quantity.build_quantity_class.<locals>.Quantity
        The specific turbulent dissipation energy as a function of height.

    '''
    # return expected dimensional unit types
    speed = 1 * unit.meter / unit.second
    speed_type = type(speed)

    turbulant_energy = 1 * unit.meter ** 2 / unit.second ** 2
    turbulant_energy_type = type(turbulant_energy)

    # Check if the inputs have units, if not, assume the units are
    # default SI units, i.e. meters for distance, meters/second for speed etc
    if not isinstance(u, speed_type):
        u = u * speed

    if not isinstance(tke, turbulant_energy_type):
        tke = tke * turbulant_energy

    if debug:
        print(u)
        print(tke)

    cmu = 0.09  # turbulence model constant

    velocity_gradient = np.gradient(u)
    epsilon = (cmu ** (1 / 2)) * tke * velocity_gradient
    omega = epsilon / (cmu * tke)

    # If a raw numpy array is needed, we can simply ask for the same array
    # stripped of its units
    if return_without_units:
        omega = np.array(omega)

    return omega


def get_eurocode_minimum_height(unit, z0):
    @unit.check('[length]')
    def unit_check(z0):
        if z0.check('[length]'):
            original_unit = z0.units
            z0.to(unit.meter)
            z0 = z0.magnitude
            return [z0, original_unit]

    check = unit_check(z0)
    x = [0.003, 0.01, 0.05, 0.3, 1.0]
    y = [1, 1, 12, 5, 10]

    interpolated_value = np.interp(check[0], x, y)

    interpolated_value = interpolated_value * unit.meter
    interpolated_value = interpolated_value.to(check[1])
    return interpolated_value


def eurocode_meteo_corrector(unit,
                             reference_speed,
                             reference_height,
                             blend_height,
                             aerodynamic_roughness,
                             reference_roughness=0.05,
                             return_without_units=False):
    '''
    Take reference values, return the meteological correction factor

    Parameters
    ----------
    unit : pint.registry.UnitRegistry
        A unit registary to do the dimensional calculations.
        
    reference_speed : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The reference speed taken at the reference height, 
        usually taken to be 10m in SimScale. If no dimenson is supplied
        we assume meters per second.
        
    reference_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The height in which we measure the reference speed,
        usually taken to be 10m/s in SimScale. If no dimenson is supplied
        we assume meters.
        
    blend_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        Like the reference height, but higher, considered to be the height
        in which the local roughness no longer effects the metological reading.
        
    aerodynamic_roughness : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The aerodynamic roughness of the AbL profile. 
        
    reference_roughness : float or pint.quantity.build_quantity_class.<locals>.Quantity, optional
        The roughness of the undesterbed boundary layer, not influenced
        by local roughness. The default is 0.05.

    Returns
    -------
    corrector : float or pint.quantity.build_quantity_class.<locals>.Quantity, optional
        A dimensionless corrector used to correct for the metological readings.

    '''
    numerator = (u_eurocode(unit,
                            reference_speed,
                            reference_height,
                            blend_height,
                            reference_roughness,
                            return_without_units=return_without_units)
                 / reference_speed)

    denominator = (u_eurocode(unit,
                              reference_speed,
                              reference_height,
                              blend_height,
                              aerodynamic_roughness,
                              return_without_units=return_without_units)
                   / reference_speed)

    corrector = numerator / denominator

    return corrector


def log_law_meteo_corrector(unit,
                            reference_speed,
                            reference_height,
                            blend_height,
                            aerodynamic_roughness,
                            reference_roughness=0.05,
                            return_without_units=False):
    '''
    Take reference values, return the meteological correction factor

    Parameters
    ----------
    unit : pint.registry.UnitRegistry
        A unit registary to do the dimensional calculations.
        
    reference_speed : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The reference speed taken at the reference height, 
        usually taken to be 10m in SimScale. If no dimenson is supplied
        we assume meters per second.
        
    reference_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The height in which we measure the reference speed,
        usually taken to be 10m/s in SimScale. If no dimenson is supplied
        we assume meters.
        
    blend_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        Like the reference height, but higher, considered to be the height
        in which the local roughness no longer effects the metological reading.
        
    aerodynamic_roughness : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The aerodynamic roughness of the AbL profile. 
        
    reference_roughness : float or pint.quantity.build_quantity_class.<locals>.Quantity, optional
        The roughness of the undesterbed boundary layer, not influenced
        by local roughness. The default is 0.05.

    Returns
    -------
    corrector : float or pint.quantity.build_quantity_class.<locals>.Quantity, optional
        A dimensionless corrector used to correct for the metological readings.

    '''
    numerator = (u_log_law(unit,
                           reference_speed,
                           reference_height,
                           blend_height,
                           reference_roughness,
                           return_without_units=return_without_units)
                 / reference_speed)

    denominator = (u_log_law(unit,
                             reference_speed,
                             reference_height,
                             blend_height,
                             aerodynamic_roughness,
                             return_without_units=return_without_units)
                   / reference_speed)

    corrector = numerator / denominator

    return corrector


def power_law_meteo_corrector(unit,
                              reference_speed,
                              reference_height,
                              blend_height,
                              alpha,
                              reference_alpha=0.115,
                              return_without_units=False):
    '''
    Take reference values, return the meteological correction factor

    Parameters
    ----------
    unit : pint.registry.UnitRegistry
        A unit registary to do the dimensional calculations.
        
    reference_speed : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The reference speed taken at the reference height, 
        usually taken to be 10m in SimScale. If no dimenson is supplied
        we assume meters per second.
        
    reference_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The height in which we measure the reference speed,
        usually taken to be 10m/s in SimScale. If no dimenson is supplied
        we assume meters.
        
    blend_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
        Like the reference height, but higher, considered to be the height
        in which the local roughness no longer effects the metological reading.
        
    alpha : float or pint.quantity.build_quantity_class.<locals>.Quantity
        The alpha of the AbL profile. 
        
    reference_alpha : float or pint.quantity.build_quantity_class.<locals>.Quantity, optional
        The alpha of the undesterbed boundary layer, not influenced
        by local roughness. The default is 0.05.

    Returns
    -------
    corrector : float or pint.quantity.build_quantity_class.<locals>.Quantity, optional
        A dimensionless corrector used to correct for the metological readings.

    '''
    numerator = (u_power_law(unit,
                             reference_speed,
                             reference_height,
                             blend_height,
                             reference_alpha,
                             return_without_units=return_without_units)
                 / reference_speed)

    denominator = (u_power_law(unit,
                               reference_speed,
                               reference_height,
                               blend_height,
                               alpha,
                               return_without_units=return_without_units)
                   / reference_speed)

    corrector = numerator / denominator

    return corrector


def generic_power_law(reference,
                      reference_z,
                      exponent,
                      z):
    '''
    

    Parameters
    ----------
    reference : float
        A reference value to use in the power law.
        
    reference_z : float
        A reference .
    exponent : TYPE
        DESCRIPTION.
    z : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    '''
    return reference * (z / reference_z) ** -exponent


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class OrderError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    message = ""

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
