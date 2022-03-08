path = r"C:\Users\DarrenLynch\Downloads\Simscale (1)\Simscale"
_run = True
meteo_speed = 10
direction = 45

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

    read_speed_code = subprocess.Popen(['simscale-eba',
                                        'cast-speed',
                                        path,
                                        str(direction),
                                        str(meteo_speed)],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       startupinfo=si)

    output, error = read_speed_code.communicate()
    output = output.decode("utf-8")
    error = error.decode("utf-8")
    cleaned_error = error.replace("Exception", "")

    if (error != None) and (cleaned_error != ""):
        raise Exception(error)
    else:
        speed = list_to_tree(ast.literal_eval(output))
