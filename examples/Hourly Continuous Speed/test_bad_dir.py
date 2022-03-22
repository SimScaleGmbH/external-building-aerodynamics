# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 17:30:28 2022

@author: DarrenLynch
"""
import simscale_eba.PedestrianWindComfort as pwc
import pathlib

import pandas as pd
import numpy as np

def round_direction(path, direction):
    path = pathlib.Path(path)

    df = pd.read_feather(path)
    df = df.set_index("index", drop=True)
    columns = df.columns.astype(float).to_numpy()

    columns.sort()
    columns = np.append(columns, columns[0] + 360)

    interval = []
    for i in range(0, len(columns) - 1):
        interval.append((columns[i] + columns[i + 1]) / 2)

    direction_bin = None
    for i in range(0, len(interval)):
        if i == 0:
            if direction < interval[i] or direction >= interval[-1]:#Remember to add th >=
                direction_bin = i
                break
        else:
            if direction >= interval[i - 1] and direction < interval[i]:
                direction_bin = i
                break

    rounded_direction = columns[direction_bin]

    return rounded_direction

field_path = pathlib.Path("E:/Current Cases/Grasshopper Plugin/dimensionless_UMag0.result")
rounded_direction = round_direction(field_path, 345)