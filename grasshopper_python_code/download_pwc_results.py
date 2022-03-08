project = "Outdoor Comfort Example"
simulation = "Pedestrian Wind Comfort"
run = "Run 1"
path = "E:\Current Cases\Grasshopper Plugin"
resolution = 5
_run = True

# Start of GH code
import subprocess

if project == None:
    raise Exception("project name is undefined")
if simulation == None:
    raise Exception("simulation name is undefined")
if run == None:
    raise Exception("run name is undefined")
if path == None:
    raise Exception("path is undefined")
if resolution == None:
    raise Exception(
        "resolution is undefined, should be >=0m, but best bellow 10m")
if _run == None:
    raise Exception("_run is undefined, should be boolean")
if not _run:
    string = "to start downloading, toggle _run to True"
    output = string
    raise Warning(string)

if _run:
    # Hide the cmd window
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    ##call the main cli function to download and process results
    download_return_code = subprocess.Popen(['simscale-eba',
                                             'download-pwc-results',
                                             project,
                                             simulation,
                                             run,
                                             str(resolution),
                                             path],
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            startupinfo=si)

    output, error = download_return_code.communicate()
    output = output.decode("utf-8")
    error = error.decode("utf-8")
    cleaned_error = error.replace("Exception", "")

    if (error != None) and (cleaned_error != ""):
        raise Exception(error)
