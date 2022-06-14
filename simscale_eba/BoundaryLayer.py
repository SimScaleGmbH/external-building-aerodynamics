import pathlib

import numpy as np
import pandas as pd
import pint as pt
from scipy import optimize

import simscale_eba.AblProfileFunctions as abl


def power_law(reference_intensity, reference_z, exponent, z):
    return reference_intensity * (z / reference_z) ** -exponent


class AtmosphericBoundaryLayer():

    def __init__(self,
                 aerodynamic_roughness=None,
                 blend_aerodynamic_roughness=0.05,
                 reference_height=10,
                 zero_height=0,
                 reference_speed=10,
                 blend_height=200,
                 angle_latitude=30,
                 alpha=None,
                 blend_alpha=0.115,
                 return_without_units=False
                 ):

        ''' 
        other set variables
        -----------------------
        '''
        self.return_without_units = return_without_units
        self.unit = pt.UnitRegistry()

        ''' 
        set reference variables
        -----------------------
        '''
        self.zero_height = zero_height
        self._aerodynamic_roughness = aerodynamic_roughness
        self._blend_aerodynamic_roughness = blend_aerodynamic_roughness
        self._reference_height = reference_height * self.unit.meter
        self._blend_height = blend_height * self.unit.meter
        self._reference_speed = reference_speed * (self.unit.meter/self.unit.second)
        self._angle_latitude = angle_latitude

        ''' 
        calculated reference variables
        ------------------------------
        '''
        self._theta = 72.9e-6
        self._f = 2 * self._theta * np.sin(np.radians(self._angle_latitude))

        self.alpha = alpha
        self.reference_alpha = blend_alpha
        self.meteo_corrector = None

        ''' 
        Height dependent profiles
        -------------------------
        '''
        x_ = np.arange(np.sqrt(self.zero_height), np.sqrt(300), (np.sqrt(300) - np.sqrt(0.3)) / 1000)
        self._height = x_ ** 2

        self._u = []
        self._v = []
        self._w = []

        self._tke = []  # turbulent kinetic energy
        self._epsilon = []
        self._omega = []

        self._intensity = []

        self._reference_intensity = []
        self._intensity_exponent = []
        self._intensity_u = []
        self._intensity_v = []
        self._intensity_w = []

        self._length_scale = []

        self._reference_length_scale = []
        self._length_scale_exponent = []
        self._length_scale_xx = []
        self._length_scale_xy = []
        self._length_scale_xz = []

        ''' 
        Methods of profile generation
        -----------------------------
        '''
        self._velocity_profile_method = None
        self._intensity_profile_method = None
        self._length_scale_profile_method = None

        '''
        Initialisation method calls
        ---------------------------
        '''

    ''' 
    getters
    -------
    '''

    def get_eurocode_minimum_height(self, z0):
        x = [0.003, 0.01, 0.05, 0.3, 1.0]
        y = [1, 1, 12, 5, 10]
        return np.interp(z0, x, y)

    def get_streamwise_speed(self):
        return self._u

    def get_methods(self):
        print("Method used for Velocity Profile is {},\n".format(self._velocity_profile_method),
              "Method used for Intensity Profile is {},\n".format(self._intensity_profile_method),
              "Method used for Length Scale Profile is {},\n".format(self._length_scale_profile_method)
              )

    def get_z0_from_alpha(self):
        def fun(x, alpha):
            return 0.24 + (0.096 * np.log10(x)) + (0.016 * (np.log10(x) ** 2)) - alpha

        sol = optimize.root(fun, [0.01], self.alpha)

        z0 = sol.x[0]
        self._aerodynamic_roughness = z0

    def get_alpha_from_z0(self):
        '''
        take aerodynamic roughness, return equivilant alpha value
        
        Near-Ground Profile of Bora Wind Speed at Razdrto, Slovenia 
    
        Parameters
        ----------
        Z0 : TYPE
            DESCRIPTION.
    
        Returns
        -------
        TYPE
            DESCRIPTION.
    
        '''
        z0 = self._aerodynamic_roughness
        self.alpha = 0.24 + (0.096 * np.log10(z0)) + (0.016 * ((z0) ** 2))

    ''' 
    setters
    -------
    '''

    def set_atmospheric_boundary_layer(
            self,
            aerodynamic_roughness=0.05,
            reference_speed=20,
            reference_height=10,
            method_dict={"u": "LOGLAW",
                         "tke": "YGCJ",
                         "omega": "YGCJ"
                         }):
        '''
        Take reference values and methods, generates the abl in order.

        Parameters
        ----------
        aerodynamic_roughness : float or pint.quantity.build_quantity_class.<locals>.Quantity
            The aerodynamic roughness of the AbL profile. 
            The default is 0.05.
            
        reference_speed : float or pint.quantity.build_quantity_class.<locals>.Quantity
            The reference speed taken at the reference height, 
            usually taken to be 10m in SimScale. If no dimenson is supplied
            we assume meters per second.
            
        reference_height : float or pint.quantity.build_quantity_class.<locals>.Quantity
            The height in which we measure the reference speed,
            usually taken to be 10m/s in SimScale. If no dimenson is supplied
            we assume meters.
            
        method_dict : dict, optional
            A dictionary of methods to be used in the generation of
            the height dependent variables.
            The default is {"u": "LOGLAW",
                                         "tke": "YGCJ",
                                         "omega": "YGCJ"}.

        Returns
        -------
        None.

        '''
        self._aerodynamic_roughness = aerodynamic_roughness
        self._reference_speed = reference_speed * (self.unit.meter/self.unit.second)
        self._reference_height = reference_height * self.unit.meter

        self.set_u_star()
        self.set_streamwise_speed(method_dict["u"])
        self.set_tke(method_dict["tke"])
        self.set_omega(method_dict["omega"])

    def set_u_star(self):
        '''
        Calulate the friction velocity, based upon reference values.

        Returns
        -------
        None.

        '''
        try:
            self.alpha == None
        except:
            raise Exception("self.alpha not defined! Contact support")

        try:
            self._aerodynamic_roughness == None
        except:
            raise Exception("self._aerodynamic_roughness not defined! Contact support")

        if self._aerodynamic_roughness == None and self.alpha != None:
            self.get_z0_from_alpha()
        elif self._aerodynamic_roughness == None and self.alpha == None:
            raise Exception('Either Aerodynamic roughness or power law',
                            'alpha needs to be specified')

        self._u_star = abl.calulate_u_star(self.unit,
                                           self._reference_speed,
                                           self._reference_height,
                                           self._aerodynamic_roughness,
                                           return_without_units=self.return_without_units)

    def set_streamwise_speed(self, method):
        '''
        Take method, return velocity profile based on reference values.

        Parameters
        ----------
        method : str
            The string which represents the method, current options are:
                -LOGLAW (recomended)
                -EUROCODE.
                -POWER

        Raises
        ------
        Exception
            Raises exception if an asked for method is not supported or 
            was passed in error.

        Returns
        -------
        None.

        '''
        if isinstance(method, str):
            if method == "EUROCODE":
                self._u = abl.u_eurocode(

                    self.unit,
                    self._reference_speed,
                    self._reference_height,
                    self._height,
                    self._aerodynamic_roughness,
                    return_without_units=self.return_without_units

                )

                self.meteo_corrector = abl.eurocode_meteo_corrector(

                    self.unit,
                    self._reference_speed,
                    self._reference_height,
                    self._blend_height,
                    self._aerodynamic_roughness,
                    self._blend_aerodynamic_roughness,
                    return_without_units=self.return_without_units

                )

            elif method == "LOGLAW":
                self._u = abl.u_log_law(

                    self.unit,
                    self._reference_speed,
                    self._reference_height,
                    self._height,
                    self._aerodynamic_roughness,
                    return_without_units=self.return_without_units

                )

                self.meteo_corrector = abl.log_law_meteo_corrector(

                    self.unit,
                    self._reference_speed,
                    self._reference_height,
                    self._blend_height,
                    self._aerodynamic_roughness,
                    self._blend_aerodynamic_roughness,
                    return_without_units=self.return_without_units

                )

            elif method == "POWER":
                self._u = abl.u_power_law(

                    self.unit,
                    self._reference_speed,
                    self._reference_height,
                    self._height,
                    self.alpha,
                    return_without_units=self.return_without_units

                )

                self.meteo_corrector = abl.power_law_meteo_corrector(

                    self.unit,
                    self._reference_speed,
                    self._reference_height,
                    self._blend_height,
                    self.alpha,
                    self.reference_alpha,
                    return_without_units=self.return_without_units

                )

            else:
                raise Exception("{} was not a valid input".format(method))

            self._velocity_profile_method = method

    def set_intensity(self, method):
        '''
        Take method, return velocity profile based on reference values.

        Parameters
        ----------
        method : str
            The string which represents the method, current options are:
                -EUROCODE.

        Raises
        ------
        Exception
            Raises exception if an asked for method is not supported or 
            was passed in error..

        Returns
        -------
        None.

        '''
        if isinstance(method, str):
            if method == "EUROCODE":
                self._intensity = abl.i_eurocode(self.unit,
                                                 self._height,
                                                 self._aerodynamic_roughness,
                                                 return_without_units=True)

            else:
                raise Exception("{} was not a valid input".format(method))

            self._intensity_profile_method = method

    def set_tke(self, method="YGCJ", tke=None, c1=0, c2=1):
        '''
        Take method, return TKE profile based on reference values.

        Parameters
        ----------
        method : str, optional
            The string which represents the method, current options are:
                -DERIVED
                -UNIFORM.
                -YGCJ (recomended)
                
            The default is "YGCJ".
            
        tke : float or pint.quantity.build_quantity_class.<locals>.Quantity, optional.
            A value of TKE for the uniform velocity profile.
            
            The default is None.
            
        c1 : float, optional
             fitting coefficient 1. The default is 0.
            
        c2 : float, optional
             fitting coefficient 2. The default is 1.

        Raises
        ------
        Exception
            Raises exception if an asked for method is not supported or 
            was passed in error..

        Returns
        -------
        None.

        '''
        if isinstance(method, str):
            if method == "DERIVED":
                self._tke = abl.tke_derived(self.unit,
                                            self._u,
                                            self._intensity,
                                            return_without_units=self.return_without_units)

            elif method == "UNIFORM":
                self._tke = abl.tke_uniform(self.unit,
                                            self._height,
                                            tke,
                                            return_without_units=self.return_without_units)

            elif method == "YGCJ":
                self._tke = abl.tke_YGCJ(self.unit,
                                         self._reference_speed,
                                         self._reference_height,
                                         self._height,
                                         self._aerodynamic_roughness,
                                         c1, c2,
                                         return_without_units=self.return_without_units)

            else:
                raise Exception("{} was not a valid input".format(method))

    def set_omega(self, method="YGCJ"):
        '''
        Take method, return omega profile based on reference values.
        
        Parameters
        ----------
        method : str, optional
            The string which represents the method, current options are:
                -YGCJ (recomended)
                -AIJ (based on velocity gradient)
                
            The default is "YGCJ".

        Raises
        ------
        Exception
            Raises exception if an asked for method is not supported or 
            was passed in error..

        Returns
        -------
        None.

        '''
        if isinstance(method, str):
            if method == "YGCJ":
                self._omega = abl.omega_YGCJ(

                    self.unit,
                    self._reference_speed,
                    self._reference_height,
                    self._height,
                    self._aerodynamic_roughness,
                    return_without_units=self.return_without_units

                )

            elif method == "AIJ":
                self._omega = abl.omega_AIJ(

                    self.unit,
                    self._u,
                    self._tke,
                    return_without_units=self.return_without_units

                )
            else:
                raise Exception("{} was not a valid input".format(method))

    def set_intensity_components(self, method, alpha=[0.1, 0.1, 0.1], reference=[0.2, 0.2, 0.2]):
        '''
        Take method, calulate turbulant intensity components.

        Parameters
        ----------
        method : str, optional
            The string which represents the method, current options are:
                -POWER (recomended)
                
            The default is "YGCJ".
            
        alpha : list, optional
            Only applicable for POWER method.
            
            A list of the alpha values for each of the 3 components. 
            The default is [0.1, 0.1, 0.1].
            
        reference : list, optional
            Only applicable for POWER method.
            
            A list of reference values for each of the 3 components. 
            The default is [0.2, 0.2, 0.2].

        Raises
        ------
        Exception
            Raises exception if an asked for method is not supported or 
            was passed in error.

        Returns
        -------
        None.

        '''
        if isinstance(method, str):
            if method == "POWER":
                self._reference_intensity = reference
                self._intensity_exponent = alpha

                self._intensity_u = abl.generic_power_law(
                    self._reference_intensity[0],
                    self._reference_height,
                    self._intensity_exponent[0],
                    self._height)

                self._intensity_v = abl.generic_power_law(
                    self._reference_intensity[1],
                    self._reference_height,
                    self._intensity_exponent[1],
                    self._height)

                self._intensity_w = abl.generic_power_law(
                    self._reference_intensity[2],
                    self._reference_height,
                    self._intensity_exponent[2],
                    self._height)
            else:
                raise Exception("{} was not a valid input".format(method))

    def set_length_scale_components(self,
                                    method,
                                    alpha=[0.1, 0.1, 0.1],
                                    reference=[0.2, 0.2, 0.2],
                                    reference_height=None
                                    ):
        '''
        Take method, calulate turbulant length scale components.

        Parameters
        ----------
        method : str, optional
            The string which represents the method, current options are:
                -POWER
            
        alpha : list, optional
            Only applicable for POWER method.
            
            A list of the alpha values for each of the 3 components. 
            The default is [0.1, 0.1, 0.1].
            
        reference : list, optional
            Only applicable for POWER method.
            
            A list of reference values for each of the 3 components. 
            The default is [0.2, 0.2, 0.2].
            
        reference_height : float, optional
            Only define if different to the reference height used in the
            velovity calculate, if not different, use None. This is 
            necessary for some validation cases.
            
            The default is None.

        Raises
        ------
        Exception
            Raises exception if an asked for method is not supported or 
            was passed in error.

        Returns
        -------
        None.

        '''
        if isinstance(method, str):
            if method == "POWER":
                if reference_height == None:
                    reference_height = self._reference_height
                self._reference_length_scale = reference
                self._length_scale_exponent = alpha

                self._length_scale_xx = abl.generic_power_law(
                    self._reference_length_scale[0],
                    reference_height,
                    self._length_scale_exponent[0],
                    self._height)

                self._length_scale_xy = abl.generic_power_law(
                    self._reference_length_scale[1],
                    reference_height,
                    self._length_scale_exponent[1],
                    self._height)

                self._length_scale_xz = abl.generic_power_law(
                    self._reference_length_scale[2],
                    reference_height,
                    self._length_scale_exponent[2],
                    self._height)
            else:
                raise Exception("{} was not a valid input".format(method))

    ''' 
    methods
    -------
    '''

    def generate_abl_monitorpoints(self):
        pass

    ''' 
    convertors
    -------
    '''
    
    def get_correction_factor(self, speed, height=10):
        
        method = self._velocity_profile_method
        
        height = height * self.unit.meter
        speed = speed * (self.unit.meter/self.unit.second)
        
        if isinstance(method, str):
            if method == "EUROCODE":
                speed_at_height = abl.u_eurocode(

                    self.unit,
                    self._reference_speed,
                    self._reference_height,
                    height,
                    self._aerodynamic_roughness,
                    return_without_units=self.return_without_units

                )

            elif method == "LOGLAW":
                speed_at_height = abl.u_log_law(

                    self.unit,
                    self._reference_speed,
                    self._reference_height,
                    height,
                    self._aerodynamic_roughness,
                    return_without_units=self.return_without_units

                )

            elif method == "POWER":
                speed_at_height = abl.u_power_law(

                    self.unit,
                    self._reference_speed,
                    self._reference_height,
                    height,
                    self.alpha,
                    return_without_units=self.return_without_units

                )

            else:
                raise Exception("{} was not a valid input".format(method))
        
        
        
        cor = corrections()
        cor.referrence_speed = self._reference_speed
        cor.reference_height = self._reference_height
        cor.correction_speed = speed_at_height
        cor.correction_height = height
        cor.speed_correction_factor = speed / speed_at_height
        cor.pressure_correction_factor = speed**2 / speed_at_height**2
                
        return cor

    def to_csv(self, path=pathlib.Path.cwd(), _list=["u", "tke", "omega"]):
        '''
        take list of variables, write them as a csv.

        Parameters
        ----------
        path : pathlib.Path
            path in which to save to, should inclue file name such as
            name.csv. Default is pathlib.Path.cwd()
        _list : list
            a list of variables in the AtmosphericBoundaryLayer to export
            as colums.

        Returns
        -------
        path : pathlib.Path
            The path that was saved to. Default is pathlib.Path.cwd()

        '''
        df = self.to_dataframe(_list)
        df.to_csv(path, index=False)
        return path

    def to_dataframe(self, _list=["u", "tke", "omega"]):
        '''
        take list of variables, return them in a pandas DataFrame.

        Parameters
        ----------
        _list : list
            a list of variables in the AtmosphericBoundaryLayer to export
            as colums.

        Returns
        -------
        DataFrame
            A pandas.DataFrame object with the requested variables, and
            the height column.

        '''

        distance = 1 * self.unit.meter
        speed = 1 * self.unit.meter / self.unit.second
        tke = 1 * self.unit.meter ** 2 / self.unit.second ** 2
        omega = 1 / self.unit.second
        dimensionless = 1 * self.unit.meter / self.unit.meter

        data_dict = {
            "u": {"data": self._u, "unit": speed},
            "tke": {"data": self._tke, "unit": tke},
            "omega": {"data": self._omega, "unit": omega},
            "Iu": {"data": self._intensity_u, "unit": dimensionless},
            "Iv": {"data": self._intensity_v, "unit": dimensionless},
            "Iw": {"data": self._intensity_w, "unit": dimensionless},
            "Lu": {"data": self._length_scale_xx, "unit": distance},
            "Lv": {"data": self._length_scale_xy, "unit": distance},
            "Lw": {"data": self._length_scale_xz, "unit": distance},
        }

        array = np.reshape(self._height, (-1, 1))
        columns = ["Height"]

        for variable in _list:
            try:
                if data_dict[variable]["data"].units != dimensionless.units:
                    data = data_dict[variable]["data"].to(data_dict[variable]["unit"])
                    data = data / data_dict[variable]["unit"]
            except:
                data = data_dict[variable]["data"]

            array = np.concatenate((array, np.reshape(data, (-1, 1))), axis=1)
            columns.append(variable)

        return pd.DataFrame(np.array(array), columns=columns)

    def to_line(self, ax):
        pass

    ''' 
    ---
    End
    '''
class corrections():
    
    def __init__(self):
        
        self.reference_height = None
        self.correction_height = None
        
        self.referrence_speed = None
        self.correction_speed = None
        
        self.speed_correction_factor = None
        self.pressure_correction_factor = None