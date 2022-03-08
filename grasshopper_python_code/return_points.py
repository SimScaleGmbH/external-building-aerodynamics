# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 15:42:09 2021

@author: DarrenLynch
"""
path = r"E:\Current Cases\WSP\working_dir\Lower"
_run = True
# reference_speed = 10
# direction = 45

import ast
# Start of GH code
import subprocess


def list_to_tree(input, none_and_holes=True, source=[0]):
    """Transforms nestings of lists or tuples to a Grasshopper DataTree"""
    from Grasshopper import DataTree as Tree
    from Grasshopper.Kernel.Data import GH_Path as Path
    from System import Array
    def proc(input, tree, track):
        path = Path(Array[int](track))
        if len(input) == 0 and none_and_holes: tree.EnsurePath(path); return
        for i, item in enumerate(input):
            if hasattr(item, '__iter__'):  # if list or tuple
                track.append(i);
                proc(item, tree, track);
                track.pop()
            else:
                if none_and_holes:
                    tree.Insert(item, path, i)
                elif item is not None:
                    tree.Add(item, path)

    if input is not None: t = Tree[object]();proc(input, t, source[:]);return t


if _run:
    # Hide the cmd window
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    read_x_code = subprocess.Popen(['simscale-eba',
                                    'cast-ordinate',
                                    path,
                                    'X'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   startupinfo=si)

    output, error = read_x_code.communicate()
    output = output.decode("utf-8")

    cleaned_error = error.replace("Exception", "")

    if (error != None) and (cleaned_error != ""):
        raise Exception(error)

    X = list_to_tree(ast.literal_eval(output))

    read_y_code = subprocess.Popen(['simscale-eba',
                                    'cast-ordinate',
                                    path,
                                    'Y'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   startupinfo=si)

    output, error = read_y_code.communicate()
    output = output.decode("utf-8")

    cleaned_error = error.replace("Exception", "")

    if (error != None) and (cleaned_error != ""):
        raise Exception(error)

    Y = list_to_tree(ast.literal_eval(output))

    read_z_code = subprocess.Popen(['simscale-eba',
                                    'cast-ordinate',
                                    path,
                                    'Z'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   startupinfo=si)

    output, error = read_z_code.communicate()
    output = output.decode("utf-8")

    cleaned_error = error.replace("Exception", "")

    if (error != None) and (cleaned_error != ""):
        raise Exception(error)

    Z = list_to_tree(ast.literal_eval(output))
