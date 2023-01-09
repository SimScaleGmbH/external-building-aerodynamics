# -*- coding: utf-8 -*-
"""
Created on Thu Jul  1 15:46:51 2021

@author: DarrenLynch
"""


class RegionOfInterest():

    def __init__(self,
                 centre=[0, 0],
                 radius=300,
                 ground_height=0,
                 north_orientation=0,
                 tallest_building_height=200,  # in meters
                 tunnel_size="moderate"):

        self._centre = centre
        self._radius = radius
        self._ground_height = ground_height
        self._north_orientation = north_orientation
        self._tallest_building_height = tallest_building_height
        self._tunnel_size = tunnel_size

        self._wt_width = None
        self._wt_length = None
        self._wt_height = None

        self._wt_maximum_point = None
        self._wt_minimum_point = None

        self._IS_TUNNEL_CREATED = False

        self._H = None
        self._S = None
        self._I = None
        self._O = None

    def set_windtunnel_size(self, height_extension=300, 
                            side_extension=300, 
                            inflow_extension=300, 
                            outflow_extension=900):
        if self._tunnel_size == "moderate":
            H, S, I, O = 3, 3, 3, 9

            self._H = H * self._tallest_building_height
            self._S = S * self._tallest_building_height
            self._I = I * self._tallest_building_height
            self._O = O * self._tallest_building_height

        elif self._tunnel_size == "large":
            H, S, I, O = 5, 5, 5, 15

            self._H = H * self._tallest_building_height
            self._S = S * self._tallest_building_height
            self._I = I * self._tallest_building_height
            self._O = O * self._tallest_building_height

        elif self._tunnel_size == "custom":
            H, S, I, O = height_extension, side_extension, inflow_extension, outflow_extension
        else:
            raise ValueError(
                "Wind Tuneel Size '{}' does not exist, use moderate, large or custom".format(self.__tunnel_size))

        self._wt_width = 2 * self._radius + 2 * self._S
        self._wt_length = 2 * self._radius + self._I + self._O
        self._wt_height = self._tallest_building_height + self._H

        self._wt_maximum_point = [
            self._centre[0] + self._radius + self._O,
            self._centre[1] + self._radius + self._S,
            self._ground_height + self._H
        ]

        self._wt_minimum_point = [
            self._centre[0] - self._radius - self._I,
            self._centre[1] - self._radius - self._S,
            self._ground_height
        ]

        self._IS_TUNNEL_CREATED = True

    def set_radius(self, radius):
        self._radius = radius
        if self._IS_TUNNEL_CREATED:
            self.set_windtunnel_size(H=self._H, S=self._S, I=self._I, O=self._O)

    def set_centre(self, centre):
        self._centre = centre
        if self._IS_TUNNEL_CREATED:
            self.set_windtunnel_size(H=self._H, S=self._S, I=self._I, O=self._O)

    def set_height(self, ground_height):
        self._ground_height = ground_height
        if self._IS_TUNNEL_CREATED:
            self.set_windtunnel_size(H=self._H, S=self._S, I=self._I, O=self._O)

    def set_north_orientation(self, north_orientation):
        self._north_orientation = north_orientation
        if self._IS_TUNNEL_CREATED:
            self.set_windtunnel_size(H=self._H, S=self._S, I=self._I, O=self._O)

    def set_tallest_building_height(self, tallest_building_height):
        self._tallest_building_height = tallest_building_height
        if self._IS_TUNNEL_CREATED:
            self.set_windtunnel_size(H=self._H, S=self._S, I=self._I, O=self._O)

    def set_tunnel_size(self, tunnel_size):
        self._tunnel_size = tunnel_size
        if self._IS_TUNNEL_CREATED:
            self.set_windtunnel_size(H=self._H, S=self._S, I=self._I, O=self._O)
