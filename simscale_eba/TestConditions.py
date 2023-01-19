# -*- coding: utf-8 -*-
"""
Created on Fri Jul  2 17:52:11 2021

@author: DarrenLynch
"""
import ladybug.epw as epw
import numpy as np

import pathlib
import copy

import simscale_eba.BoundaryLayer as abl


class WindData():

    def __init__(self):
        self._directions = []
        self._atmospheric_boundary_layers = {}
        self._weather_periods = WeatherPeriods

        self._hourly_wind_speed = []
        self._hourly_direction = []
        self._hourly_timestamp = []

        self.reference_speeds = {}
        self.aerodynamic_roughnesses = {}
        self.reference_heights = {}
        self.meteo_correctors = {}
        self.directions = []
        
        self.dwt_paths = {}
        self.dwt_objects = {}
        self.dwt_roi = {}

    def set_atmospheric_boundary_layer(self,
                                       direction,
                                       AtmosphericBoundaryLayer):
        '''
        take an atmospheric boundary layer object and assign it directionly

        Parameters
        ----------
        direction : float
            A direction, clockwise from north as an angle in degrees.
        AtmosphericBoundaryLayer : AtmosphericBoundaryLayer object
            An atmospheric boundary layer object as a definition of the
            definition of the variation of velocity and turbulance, with 
            respect to height.

        Returns
        -------
        None.

        '''
        self._atmospheric_boundary_layers[
            "{}".format(direction)] = AtmosphericBoundaryLayer

        self.reference_speeds[
            "{}".format(direction)
        ] = AtmosphericBoundaryLayer._reference_speed

        self.aerodynamic_roughnesses[
            "{}".format(direction)
        ] = AtmosphericBoundaryLayer._aerodynamic_roughness

        self.reference_heights[
            "{}".format(direction)
        ] = AtmosphericBoundaryLayer._reference_height

        self.meteo_correctors[
            "{}".format(direction)
        ] = AtmosphericBoundaryLayer.meteo_corrector

        self.directions = np.array(
            list(self._atmospheric_boundary_layers.keys())).astype(float)

    def get_directions(self):
        '''
        return the directions already defined as a key object

        Returns
        -------
        key object
            A key object of the directions already defined.

        '''
        self._directions = self._atmospheric_boundary_layers.keys()
        return self._directions

    def import_epw(self, epw_file):
        '''
        Take a path to an EPW, store the wind direction and speed

        Parameters
        ----------
        epw_file : pathlib.Path
            A path to the epw to read.

        Returns
        -------
        epw_data : EPW object
            The EPW object from ladybug tools.

        '''
        epw_data = epw.EPW(epw_file)
        self._hourly_wind_speed = epw_data.wind_speed
        self._hourly_direction = epw_data.wind_direction
        return epw_data
    
    def create_roi_for_dwt(self,
                           direction,
                           roi,
                           nddwt):
        '''
        Create an Region of Interest object for each direction from DWT

        Parameters
        ----------
        direction : float
            An angle from north.
        roi : RegionOfInterest
            A region of Interest object.
        nddwt : non_diectional_dwt
            A non directional wind tunnel.

        Returns
        -------
        None.

        '''
        
        self.dwt_roi['{}'.format(direction)] = copy.deepcopy(roi)
        self.dwt_roi['{}'.format(direction)].set_windtunnel_size(dwt=nddwt)

    def set_atmospheric_boundary_layers(self,
                                        directions=np.arange(0, 360, 30).tolist(),
                                        surface_roughness_list=(0.3 * np.ones(12)).tolist(),
                                        reference_speeds=(10 * np.ones(12)).tolist(),
                                        reference_heights=(10 * np.ones(12)).tolist(),
                                        method_dict={"u": "LOGLAW",
                                                     "tke": "YGCJ",
                                                     "omega": "YGCJ"
                                                     },
                                        return_without_units=False):
        '''
        Take a batch of parameters, set them in the wind conditions object

        Parameters
        ----------
        directions : np.array, optional
            an array of directions. 
            
            The default is np.arange(0, 360, 30).tolist().
            
        surface_roughness_list : np.array, optional
            An array of surface rougnesses, length should be the same as 
            directions. 
            
            The default is (0.3*np.ones(12)).tolist().
            
        reference_speeds : np.array, optional
            An array of reference speeds, length should be the same as 
            directions.
            
            The default is (10*np.ones(12)).tolist().
            
        reference_heights : TYPE, optional
            An array of reference heights, length should be the same as 
            directions.. 
            
            The default is (10*np.ones(12)).tolist().
            
        method_dict : dict, optional
            A dictonary with the methods to calulate the key parameters
            u, velocity (streamwise), tke, Turbulant Kinetic Energy, 
            and omega, the specific disipation rate. 
            
            The default is {"u": "LOGLAW",                                 
                            "tke": "YGCJ",                                 
                            "omega": "YGCJ"                                 
                            }.

        Returns
        -------
        None.

        '''
        for (_dir,
             z0,
             reference_speed,
             reference_height) in (zip(directions,
                                       surface_roughness_list,
                                       reference_speeds,
                                       reference_heights)):
            profile = abl.AtmosphericBoundaryLayer(
                return_without_units=return_without_units)

            profile.set_atmospheric_boundary_layer(
                aerodynamic_roughness=z0,
                reference_speed=reference_speed,
                reference_height=reference_height,
                method_dict=method_dict)

            self.set_atmospheric_boundary_layer(str(_dir), profile)
            
    def set_digital_wind_tunnels(self,
                                 roi,
                                 path = pathlib.Path.cwd(),
                                 directions=np.arange(0, 360, 30).tolist(),
                                 surface_roughness_list=(0.3 * np.ones(12)).tolist(),
                                 reference_speeds=(15 * np.ones(12)).tolist(),
                                 return_without_units=False):
        
        from dwt.create_dwt import non_diectional_dwt
        
        for (_dir,
             z0,
             reference_speed) in (zip(directions,
                                       surface_roughness_list,
                                       reference_speeds)):
            
            directionless_digital_wind_tunnel = non_diectional_dwt(z0)
            
            (path / '{}'.format(_dir)).mkdir(parents=True, exist_ok=True)
            
            dwt_object = directionless_digital_wind_tunnel.create_dwt_from_nddwt(
                direction=_dir,
                path=path / '{}'.format(_dir),
                exclusion_radius=300)
  
            self.create_roi_for_dwt(_dir, roi, 
                                    directionless_digital_wind_tunnel)
            
            self.create_dwt_geometry(_dir, dwt_object)
            
        self.set_atmospheric_boundary_layers(directions=directions,
                                             surface_roughness_list=surface_roughness_list,
                                             reference_speeds=reference_speeds,
                                             reference_heights=(10 * np.ones(len(reference_speeds))).tolist(),
                                             method_dict={"u": "UNIFORM",
                                                          "tke": "YGCJ",
                                                          "omega": "YGCJ"
                                                          },
                                             return_without_units=False)
    
    def create_dwt_geometry(self, direction, dwt_object):
        
        dwt_object.create_geometry()
        
        self.dwt_objects[direction] = dwt_object
        self.dwt_paths[direction] = dwt_object.path
        

class WeatherPeriods():

    def __init__(self):
        self._periods = {}

    def set_period(self, label, begin, end):
        self._periods["{}".format(label)] = {
            "Start time": begin,
            "End time": end
        }
