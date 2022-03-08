# -*- coding: utf-8 -*-
"""
Created on Tue Jul  6 18:07:19 2021

@author: DarrenLynch
"""
import numpy as np


def angle_to_vectors(angle):
    u = np.cos(np.radians(angle))
    v = np.sin(np.radians(angle))
    return u, v


def return_quad(u, v):
    if np.sign(u) > 0 and np.sign(v) > 0:
        return 1
    elif np.sign(u) > 0 and np.sign(v) < 0:
        return 4
    elif np.sign(u) < 0 and np.sign(v) < 0:
        return 3
    elif np.sign(u) < 0 and np.sign(v) > 0:
        return 2


def check_within_bounds(upper, lower, angle):
    u_upper, v_upper = angle_to_vectors(upper)
    u_lower, v_lower = angle_to_vectors(lower)
    u, v = angle_to_vectors(angle)

    q_upper = return_quad(u_upper, v_upper)
    q_lower = return_quad(u_lower, v_lower)

    if (q_lower > q_upper) and (((angle > lower) and (angle <= 360)) or ((angle <= upper) and (angle >= 0))):
        return True
    elif (angle <= upper) and (angle > lower):
        return True
    else:
        return False


check = check_within_bounds(270, 5, 0)
