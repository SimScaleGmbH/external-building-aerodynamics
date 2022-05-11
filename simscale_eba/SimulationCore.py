import os
import pathlib

import pandas as pd
import simscale_sdk as sim
import vtk

import simscale_eba.api_variables as api


def check_api(self):
    '''
    Check API key is set, returns boolean True if not set.

    Raises
    ------
    Exception
        If the API key and URL is not set, rasie an exception.

    Returns
    -------
    is_not_existent : boolean
        True if not set.

    '''
    is_not_existent = not os.getenv("SIMSCALE_API_KEY") or not os.getenv("SIMSCALE_API_URL")
    if is_not_existent:
        raise Exception(
            "Either `SIMSCALE_API_KEY` or `SIMSCALE_API_URL`",
            " environment variable is missing.")
        return is_not_existent
    else:
        print("SimScale API Key and URL found in environment variables.")


def create_client(self, version=0):
    '''
    Reads API key and URL and returns API clients required.
    
    It is recomended to run check_api first.
        Parameters
    ----------
    version : int
        Version of SimScale API, at time of writing, only 0 is valid.
        Default is 0.
    
    Returns
    -------
    api_client : object
        An API client that represents the user, and their login 
        credentials.
    api_key_header : object
    api_key : string
        A string that is your API key, read from the environment 
        variables.
    credential : SimscaleCredentials object
        An object contain api keys and credential information

    '''
    credentials = api.SimscaleCredentials()
    credentials.check_variables()

    api_key_header = credentials.get_api_header()
    api_key = credentials.get_api_key()
    
    configuration = credentials.get_config()

    api_client = sim.ApiClient(configuration)
    
    self.api_client = api_client
    self.api_key_header = api_key_header
    self.api_key = api_key
    self.credentials = credentials

def get_keys_from_client(self):
    configuration = self.credentials.get_config()
    
    self.api_client = sim.ApiClient(configuration)
    self.api_key_header = self.credentials.api_header
    self.api_key = self.credentials.api_key

def create_api(self):
    # API clients, needed to find project, simulation and run
    project_api = sim.ProjectsApi(self.api_client)
    simulation_api = sim.SimulationsApi(self.api_client)
    simulation_run_api = sim.SimulationRunsApi(self.api_client)
    geometry_api = sim.GeometriesApi(self.api_client)
    storage_api = sim.StorageApi(self.api_client)
    geometry_import_api = sim.GeometryImportsApi((self.api_client))
    table_import_api = sim.TableImportsApi(self.api_client)

    self.project_api = project_api
    self.simulation_api = simulation_api
    self.run_api = simulation_run_api
    self.geometry_api = geometry_api
    self.geometry_import_api = geometry_import_api
    self.storage_api = storage_api
    self.table_import_api = table_import_api
    

def find_project(self, name):
    '''
    Take a project Name, return a project

    Parameters
    ----------
    name : string
        The exact name of the project, best copied from the SimScale
        UI.
    project_api : object
        An API object that can be used for querying and creating
        SimScale projects.

    Raises
    ------
    Exception
        Raise exception if the name matches no project in the clients*
        account.

        *client is created using the users API key, see create_client.
    Returns
    -------
    found : object
        A simulation object that was matched by the provided name.

    '''
    project_api = self.project_api

    projects = project_api.get_projects(limit=1000).to_dict()['embedded']
    found = None
    for project in projects:
        if project['name'] == name:
            found = project
            print('Project found: \n' + str(found['name']))
            break
    if found is None:
        raise Exception('could not find project with name: ' + name)

    self.project_id = found['project_id']
    self.project = name


def find_simulation(self, name):
    '''
    Take a Simulation Name, return a simulation

    Parameters
    ----------
    name : string
        The exact name of the simulation, best copied from the SimScale 
        UI.
    project_id : object
        the ID of the project that you are searching, Simulations are 
        child objects of projects.
    simulation_api : object
        An API object that can be used for querying and creating 
        SimScale simulations..

    Raises
    ------
    Exception
        Raise exception if the name matches no simulation in the 
        project.

    Returns
    -------
    found : object
        A simulation object that was matched by the provided name.

    '''
    project_id = self.project_id
    simulation_api = self.simulation_api

    simulations = simulation_api.get_simulations(project_id).to_dict()['embedded']
    found = None
    for simulation in simulations:
        if simulation['name'] == name:
            found = simulation
            print('Simulation found: \n' + str(found['name']))
            break
    if found is None:
        raise Exception('could not find simulation with id: ' + name)
    self.simulation = found
    self.simulation_id = found["simulation_id"]


def find_geometry(self, name):
    '''
    Take a Simulation Name, return a simulation

    Parameters
    ----------
    name : string
        The exact name of the simulation, best copied from the SimScale
        UI.
    project_id : object
        the ID of the project that you are searching, Simulations are
        child objects of projects.
    simulation_api : object
        An API object that can be used for querying and creating
        SimScale simulations..

    Raises
    ------
    Exception
        Raise exception if the name matches no simulation in the
        project.

    Returns
    -------
    found : object
        A simulation object that was matched by the provided name.

    '''
    project_id = self.project_id
    geometry_api = self.geometry_api

    geometries = geometry_api.get_geometries(project_id).to_dict()['embedded']
    found = None
    for geometry in geometries:
        if geometry['name'] == name:
            found = geometry
            print('Geometry found: \n' + str(found['name']))
            break
    if found is None:
        raise Exception('could not find geometry with id: ' + name)
    self.geometry = found
    self.geometry_id = found["geometry_id"]


def find_run(self, name):
    '''
    Take, name, parent simulation and parent project, return run.

    Parameters
    ----------
    name : string
        The exact name of the simulation run, best copied from the 
        SimScale UI.
    project_id : object
    simulation_id : object
    simulation_run_api : object
        An API object that can be used for querying and creating and 
        downloading SimScale simulation runs.

    Raises
    ------
    Exception
        Raise exception if the name matches no run in the parent 
        simulation.

    Returns
    -------
    found : TYPE
        DESCRIPTION.

    '''
    project_id = self.project_id
    simulation_id = self.simulation_id
    simulation_run_api = self.run_api

    runs = simulation_run_api.get_simulation_runs(
        project_id, simulation_id).to_dict()['embedded']

    found = None
    for run in runs:
        if run['name'] == name:
            found = run
            print('Run found: \n' + str(found['name']))
            break
    if found is None:
        raise Exception('could not find simulation with id: ' + name)
    self.run = found
    self.run_id = found["run_id"]


def import_ladybug_grid(self, path, name):
    '''
    Take path, set grid as name

    Parameters
    ----------
    path : pathlib.Path
        A path to the ladybug grid saved as text.
    name : str
        The name which is to be assigned to the grid.

    Returns
    -------
    None.

    '''
    df = pd.read_csv(path, header=None, names=["X", "Y", "Z"])
    df['X'] = df['X'].str[1:].astype(float)
    df['Z'] = df['Z'].str[:-1].astype(float)
    df = df.rename('P{}'.format)
    self.grid[name] = {}
    self.grid[name]['data'] = df


def case_to_csv(inputPath, output_file=pathlib.Path.cwd()):
    """
    Take Ensight Gold .case file, return .csv file
    
    An ensight gold format is used for most result outputs from PWC and 
    LBM solvers. It is an open source file format that can be opened 
    by many 3rd part post processing applications. For programatic reading
    of results however, we find VTK a good paser to get the results into
    tabulated form.

    Parameters
    ----------
    inputPath : pathlib.Path
        A path to the .case file.
    outputPath : pathlib.Path, optional
        A path to the directory in which the .csv should be saved. 
        
        The default is pathlib.Path.cwd(), the current working directory.

    Returns
    -------
    None.

    """

    """Convert an ensight .case file to a CSV file."""
    output_file = pathlib.Path(output_file)
    outputPath = output_file.parent

    inputPath = pathlib.Path(inputPath)

    case = vtk.vtkEnSightGoldBinaryReader()
    case.SetCaseFileName(inputPath.as_posix())
    case.Update()

    data = case.GetOutput()

    exported_blocks = []
    number_of_blocks = data.GetNumberOfBlocks()
    for i in range(number_of_blocks):
        block_name = data.GetMetaData(i).Get(vtk.vtkCompositeDataSet.NAME())
        if "data - wind_comfort_surface" in block_name:
            pedestrian_path = data.GetBlock(i)
            point = pedestrian_path.GetPoints()

            table = vtk.vtkDataObjectToTable()
            table.SetInputData(pedestrian_path)
            table.Update()
            table.GetOutput().AddColumn(point.GetData())
            table.Update()

            writer = vtk.vtkDelimitedTextWriter()
            writer.SetInputConnection(table.GetOutputPort())

            block_output_path = outputPath / "{}.csv".format(block_name)

            writer.SetFileName(block_output_path.as_posix())
            writer.Update()
            writer.Write()

            exported_blocks.append(block_output_path)

    if len(exported_blocks) == 0:
        raise Exception('No Wind Comfort Surfaces were found, cannot proceed')

    dataframes = []
    for path in exported_blocks:
        df = pd.read_csv(path)
        dataframes.append(df)

    export_df = pd.concat(dataframes)
    export_df = export_df.reset_index(drop=True)

    export_df.to_csv(output_file)

def case_to_stl(input_path, output_path=pathlib.Path.cwd()):
    '''
    Take a .case file, exports .STL files
    
    There are several STL's that are exported:
        1. Geometry: The teselated geometry used by the solver
        2. Tree: The tesselated geometry used for the tree objects
        3. Floor: The lowest surface considered in the simulation, if
           no topology is pressent, this is the ground also.
        4. Pedestrian Level: The original STL file that results colour

    Parameters
    ----------
    inputPath : str
        the .case file to read.
    output_path : str, optional
        The path to export the STL files to. 
        
        The default is pathlib.Path.cwd().

    Returns
    -------
    None.

    '''
    #Mapping of user names, to .case file block names
    export_dict = {'Geometry' : "group-all-volumes", 
                  'Tree' : "Tree",
                  'Floor' : 'noSlipBoxVolume-ZMIN',
                  'Pedestrian Level' : 'data - wind_comfort_surface'}
    
    output_path = pathlib.Path(output_path)

    input_path = pathlib.Path(input_path)

    case = vtk.vtkEnSightGoldBinaryReader()
    case.SetCaseFileName(input_path.as_posix())
    case.Update()

    data = case.GetOutput()
    
    number_of_blocks = data.GetNumberOfBlocks()
    
    def get_block(block_name_keyword, export_name, output_path):
        filename = output_path / '{}.stl'.format(export_name)
        for i in range(number_of_blocks):
            block_name = data.GetMetaData(i).Get(vtk.vtkCompositeDataSet.NAME())
            if block_name_keyword in block_name:
                
                unstruct_grid = data.GetBlock(i)
                
                #Example here: https://gist.github.com/thewtex/8263132
                #Take the unstructured data, create a surface filter, provide
                #the unstructured grid
                surface_filter = vtk.vtkDataSetSurfaceFilter()
                surface_filter.SetInputData(unstruct_grid)
                
                triangle_filter = vtk.vtkTriangleFilter()
                triangle_filter.SetInputConnection(surface_filter.GetOutputPort())
                
                writer = vtk.vtkSTLWriter()
                writer.SetFileName(filename.as_posix())
                writer.SetInputConnection(triangle_filter.GetOutputPort())
                writer.Write()
                break
            
        return filename
            
    stl_path_dict = {}
    for key in export_dict:
        path = get_block(export_dict[key], key, output_path)
        stl_path_dict[key] = path.as_posix()
        
    return stl_path_dict