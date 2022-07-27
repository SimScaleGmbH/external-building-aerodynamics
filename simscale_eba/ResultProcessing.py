import logging
import pathlib
import shutil
import zipfile

import numpy as np
import pandas as pd
import vtk
from scipy.stats import weibull_min

import simscale_eba.SimulationCore as sc

_logger = logging.getLogger(__name__)


def probes_to_dataframe(path):
    '''
    Take a path to a downloaded probe statistic result, return a dict
    
    Parameters
    ----------
    path : pathlib.Path
        A path to the downloaded csv file from SimScale.

    Returns
    -------
    _dict : dict
        The dictionary has keys from the variables, i.e. p, UMag etc.

    '''
    raw = pd.read_csv(path, index_col="ITEM NAME")
    if isinstance(raw.index[0], str):
        raw = raw.reset_index()
        raw["ITEM NAME"] = raw['ITEM NAME'].map(lambda x: x.lstrip('P'))
        raw = raw.set_index("ITEM NAME")
        raw.index = raw.index.astype(int)

    else:
        raw = pd.read_csv(path, index_col="ITEM NAME")
        raw = raw.sort_index()

    raw = raw.sort_index()
    grouped_df = raw.groupby("VARIABLE")
    _list = list(grouped_df)
    _dict = {}
    for item in _list:
        _dict[item[0]] = item[1].drop(columns=["VARIABLE"])
    return _dict


def check_item_has_name(item, name):
    '''
    Takes item and name, returns true if no name attribute or name matches.

    Parameters
    ----------
    item : Result object
        A SimScale result object.
    name : str
        A name to compare, this would be the neame of a probe plot for
        example.

    Returns
    -------
    bool
        True if no name or name matched, false if name doesn't match.

    '''
    if name == None:
        return True
    elif hasattr(item, "name"):
        if item.name == name:
            return True
        else:
            return False
    elif not hasattr(item, "name"):
        print("Item does not contain an attribute called name")
        return True
    else:
        return False


def check_item_has_quantity(item, quantity):
    '''
    Takes item and name, returns true if no quantity attribute or quantity matches.

    Parameters
    ----------
    item : Result object
        A SimScale result object.
    name : str
        A name to compare, this would be the neame of a probe plot for
        example.

    Returns
    -------
    bool
        True if no quantity or quantity matched, false if quantity doesn't 
        match.

    '''
    if quantity == None:
        return True
    elif hasattr(item, "quantity"):
        if item.quantity == quantity:
            return True
        else:
            return False
    elif not hasattr(item, "quantity"):
        print("Item does not contain an attribute called name")
        return True
    else:
        return False


class directional_result():

    def __init__(self, credentials=None):
        self.name = None
        self.run = None
        self.results = None
        self.download_dict = None
        self.exported_results_dict = {}
        self.weather_statistics = None
        self.comfort_map = None
        
        self.credentials = credentials
        
        self.project_id = None
        self.simulation_id = None
        self.run_id = None
        self.geometry_id = None
        self.storage_id = None
        self.flow_domain_id = None
        self.wind_profile_id = {}

        self.project_api = None
        self.simulation_api = None
        self.run_api = None
        self.geometry_api = None
        self.geometry_import_api = None
        self.storage_api = None

        self.api_client = None
        self.api_key_header = None
        self.api_key = None

        # Check and create API environment
        if self.credentials == None:
            sc.create_client(self)
            
        else:
            sc.get_keys_from_client(self)
        
        sc.create_api(self)

    def get_run_from_multi_directional_result(self,
                                              multi_directional_result,
                                              direction):
        '''
        Take a single direction from a multidirectional analysis type.
        
        Mainly for internal use.

        Parameters
        ----------
        multi_directional_result : multi_directional_result object
            A multidirectional result set.
        direction : float
            The direction in degrees, clockwise from north in which to 
            extract.

        Returns
        -------
        None.

        '''
        self.project_id = multi_directional_result.project_id
        self.simulation_id = multi_directional_result.simulation_id
        self.run_id = multi_directional_result.run_ids[direction]
        self.name = str(direction)

    def find_project(self, name):
        '''
        take a name, return the project ID.

        Parameters
        ----------
        name : str
            The name of the project.

        Returns
        -------
        None.

        '''
        sc.find_project(self, name)

    def find_simulation(self, name):
        '''
        take a name, return the Simulation ID.

        Parameters
        ----------
        name : str
            The name of the simulation.

        Returns
        -------
        None.

        '''
        sc.find_simulation(self, name)

    def find_run(self, name):
        '''
        take a name, return the run ID.

        Parameters
        ----------
        name : str
            The name of the run.

        Returns
        -------
        None.

        '''
        sc.find_run(self, name)

    def query_results(self):
        '''
        saves a list of all available results.

        Returns
        -------
        None.

        '''
        project_id = self.project_id
        simulation_id = self.simulation_id
        run_id = self.run_id

        end = False
        page = 1
        individual_results = []
        while not end:
            run = self.run_api.get_simulation_run_results(project_id,
                                                          simulation_id,
                                                          run_id,
                                                          limit=1000,
                                                          page=page)

            individual_results.extend(run.embedded)

            if len(run.embedded) < 1000:
                end = True

            page += 1

        result_dict = {}
        result_types = ["PROBE_POINT_PLOT_STATISTICAL_DATA", "FORCE_PLOT", "TRANSIENT_SOLUTION", "SNAPSHOT_SOLUTION",
                        "AVERAGED_SOLUTION", "PROBE_POINT_PLOT"]
        for _type in result_types:
            result_dict[_type] = []

            for individual_result in individual_results:
                if individual_result.category == _type:
                    result_dict[_type].append(individual_result)

        self.results = result_dict

    def return_result_options(self):
        '''
        returns a key object of available types of result

        Returns
        -------
        key object
            a key object from a dictionary of all available result types.

        '''
        return self.results.keys()

    def _find_item(self, category, name=None, quantity=None):
        '''
        internal use. Takes a category, name and quantity, returns a result

        Parameters
        ----------
        category : str
            Category, for example, PROBE_POINT_PLOT_STATISTICAL_DATA.
            
        name : str, optional
            Name of the item if applicable. 
            
            The default is None.
            
        quantity : str, optional
            The quantity if applicable, for example p, is pressure. 
            
            The default is None.

        Returns
        -------
        items : TYPE
            DESCRIPTION.

        '''
        _category = self.results[category]
        items = []
        for item in _category:
            check_name = check_item_has_name(item, name)
            check_quantity = check_item_has_quantity(item, quantity)
            if check_name & check_quantity:
                items.append(item)
        return items

    def download_result(self, category=None, name=None, quantity=None, path=pathlib.Path.cwd()):
        '''
        Downloads requested results to a path.

        Parameters
        ----------
        category : str, optional
            Category, for example, PROBE_POINT_PLOT_STATISTICAL_DATA.
            
            The default is None.
            
        name : str, optional
            Name of the item if applicable.
            
            The default is None.
            
        quantity : str, optional
            The quantity if applicable, for example p, is pressure.. 
            
            The default is None.
            
        path : pathlib.Path, optional
            The path in which to download results to. 
            
            The default is pathlib.Path.cwd().

        Returns
        -------
        None.

        '''
        items = self._find_item(category, name, quantity)
        download_dict = self.download_dict
        if download_dict is None:
            download_dict = {}
        if category not in download_dict.keys():
            download_dict[category] = {}

        if name not in download_dict[category].keys():
            download_dict[category][name] = {}

        if quantity not in download_dict[category][name].keys():
            download_dict[category][name][quantity] = {}

        for item in items:
            url = item.download.url
            data_responce = self.api_client.rest_client.GET(
                url=url,
                headers={self.api_key_header: self.api_key},
                _preload_content=False
            )

            probe_point_plot_statistical_data_csv = data_responce.data.decode('utf-8')
            output_path = path / "{}_{}_{}.csv".format(category, name, self.name)

            download_dict[category][name][quantity] = output_path

            with open(output_path, 'w', newline="") as file:
                file.write(probe_point_plot_statistical_data_csv)
            file.close()

        self.download_dict = download_dict


class multi_directional_result():

    def __init__(self):
        self.project_id = None
        self.simulation_id = None
        self.run_ids = {}
        self.run_id = None

        self.external_building_assessment = None
        self.results = {}
        self.case_download_dict = {}
        self.download_dict = None
        self.exported_results_dict = {}
        self.reference_speeds = {}

        self.comfort_criteria = None

        self.project_api = None
        self.simulation_api = None
        self.run_api = None
        self.geometry_api = None
        self.geometry_import_api = None
        self.storage_api = None

        self.api_client = None
        self.api_key_header = None
        self.api_key = None

    def get_pedestrian_wind_comfort(self, project, simulation, run, path=pathlib.Path.cwd()):
        '''
        Take names, return path to downloaded results.
        
        Parameters
        ----------
        project : string
            The exact name of the project, best copied from the SimScale 
            UI.
        simulation : string
            The exact name of the simulation, best copied from the SimScale 
            UI..
        run : string
            The exact name of the simulation run, best copied from the 
            SimScale UI.
        output_folder : TYPE
            DESCRIPTION.
        Returns
        -------
        pathlib.Path
            Path to the downloaded results.
        '''
        sc.check_api(self)
        sc.create_client(self)

        sc.find_project(self, project)
        sc.find_simulation(self, simulation)
        sc.find_run(self, run)

        self.pull_run_results(output_folder=pathlib.Path.cwd())

    def pull_run_results(self, output_folder=pathlib.Path.cwd()):
        '''
        

        Parameters
        ----------
        output_folder : TYPE, optional
            DESCRIPTION. The default is pathlib.Path.cwd().

        Returns
        -------
        None.

        '''
        output = pathlib.Path(output_folder)
        output.mkdir(parents=True, exist_ok=True)

        self.get_average_direction_url()
        dict_ = self.case_download_dict

        csv_list = {}
        for key in dict_:
            case_file_path = self.download_average_direction_result(direction=key)

            self.case_to_csv(
                output.joinpath(key, case_file_path.name).as_posix(),
                output.joinpath(f'{key}.csv').as_posix())

            csv_list[key] = output.joinpath(f'{key}.csv')
            shutil.rmtree(output.joinpath(key).as_posix(), ignore_errors=True)
        self.download_dict = csv_list

    def get_average_direction_url(self):
        '''
        Take names, return a dictionary with direction and location.
        
        Parameters
        ----------
        project : string
            The exact name of the project, best copied from the SimScale 
            UI.
        simulation : string
            The exact name of the simulation, best copied from the SimScale 
            UI..
        run : string
            The exact name of the simulation run, best copied from the 
            SimScale UI.
        Returns
        -------
        dict
            A dictionary with direction in degrees from north as the key,
            and a download object as the value.
        '''
        sc.check_api(self)
        sc.create_client(self)
        simulation_run_api = self.run_api

        project_id = self.project_id
        simulation_id = self.simulation_id
        run_id = self.run_id
        results = simulation_run_api.get_simulation_run_results(
            project_id, simulation_id, run_id, limit=1000).embedded

        direction_dict = {}

        for result in results:
            if result.category == 'AVERAGED_SOLUTION':
                direction_dict[str(result.direction)] = result.download

        self.case_download_dict = direction_dict

    def download_average_direction_result(self,
                                          direction=float(0),
                                          path=pathlib.Path.cwd()):
        '''
        Take dict of directions and locations, and a direction, return results.
        Parameters
        ----------
        direction_dict : dict
            A dictionary of simscale result URL's with direction as the key.
        output_folder : path
            Folder to output results into, subfolders for each direction 
            will be created.
        direction : string, optional
            A string of the angle you wish to download, to download results
            for a Northerly wind direction specify "0.0". 
            The default is float(0).
        Returns
        -------
        is_sucessful : boolean
        '''

        api_client = self.api_client
        api_key_header = self.api_key_header
        api_key = self.api_key
        download_obj = self.case_download_dict[str(direction)]

        url = download_obj.url

        print(f'Downloading results for direction: {direction}')
        try:
            averaged_solution_response = api_client.rest_client.GET(
                url=url,
                headers={api_key_header: api_key},
                _preload_content=False
            )
            out_file = path.joinpath(f'{direction}averaged_solution.zip_')
            with out_file.open('wb') as zip__file:
                zip__file.write(averaged_solution_response.data)

            # extract data
            zip_ = zipfile.ZipFile(out_file.as_posix())
            extract_subdirectory = path.joinpath(str(direction))
            zip_.extractall(extract_subdirectory)
            zip_.close()

            # delete the file
            out_file.unlink()

            result_path = extract_subdirectory.joinpath('Directions', str(direction), 'export')

            case_file_path = ''
            for file in result_path.iterdir():
                shutil.move(file.as_posix(), extract_subdirectory.joinpath(file.name))
                if file.suffix == '.case':
                    case_file_path = file

            delete_path = extract_subdirectory.joinpath('Directions')
            shutil.rmtree(delete_path.as_posix(), ignore_errors=True)
        except:
            raise Exception('results for direction {} failed to download'.format(direction))

        return case_file_path

    def case_to_csv(self, inputPath, outputPath=pathlib.Path.cwd()):
        """Convert an ensight .case file to a CSV file."""
        case = vtk.vtkEnSightGoldBinaryReader()
        case.SetCaseFileName(inputPath)
        case.Update()

        data = case.GetOutput()

        # noBlocks = data.GetNumberOfBlocks()
        pedestrian_path = data.GetBlock(0)
        point = pedestrian_path.GetPoints()

        table = vtk.vtkDataObjectToTable()
        table.SetInputData(pedestrian_path)
        table.Update()
        table.GetOutput().AddColumn(point.GetData())
        table.Update()

        writer = vtk.vtkDelimitedTextWriter()
        writer.SetInputConnection(table.GetOutputPort())
        writer.SetFileName(outputPath)
        writer.Update()
        writer.Write()

    def make_pedestrian_wind_comfort_non_dimensional(self, input_folder=pathlib.Path.cwd(),
                                                     ref_speed=10,
                                                     output_folder=pathlib.Path.cwd()):
        """Generate local speed factor and local direction files from SimScale results.
        \b
        Args:
            folder: The location at which the directional CFD data is located in csv files
                from the vtk export.
        """

        # try:
        if not output_folder:
            output = pathlib.Path(input_folder)
        else:
            # create output folder
            output = pathlib.Path(output_folder)
            output.mkdir(parents=True, exist_ok=True)

        csv = []
        for key in self.download_dict.keys():
            csv.append(self.download_dict[key])

        local_speed, local_direction, points = self.read_directions(csv, ref_speed)

        self.exported_results_dict["UMag"] = {}
        self.exported_results_dict["UMag"]["AVG"] = {}
        self.exported_results_dict["UMag"]["AVG"]["dimensionless"] = pathlib.Path(output,
                                                                                  'dimensionless_UMag_AVG.result')

        to_file(
            local_speed,
            pathlib.Path(output, 'dimensionless_UMag_AVG.result').as_posix()
        )
        to_file(
            local_direction,
            pathlib.Path(output, 'direction.result').as_posix()
        )
        to_file(
            points,
            pathlib.Path(output, 'points.result').as_posix()
        )

    def read_directions(self, csv_list, reference_speed=10):
        '''
        Take a list of csv files, open them and make non-dimensional.
        
        This is mainly for internal use

        Parameters
        ----------
        csv_list : list
            A list of csv paths.
            
        reference_speed : float, optional
            A float representing the reference speed the simulation was 
            run at, SimScale uses 10m/s. 
            
            The default is 10.

        Returns
        -------
        speeds : np.array
            The non-dimensional speed.
        directions : np.array
            The Direction in terms of angle from north.
        points : np.array
            A cartesian coordinate in 3 dimesnions.

        '''
        labels = []
        for i, file in enumerate(csv_list):
            table = pd.read_csv(pathlib.Path(file).as_posix())
            if i == 0:
                points = table[["Points:0", "Points:1", "Points:2"]]

            u = table["Velocities_n:0"].to_numpy()
            v = table["Velocities_n:1"].to_numpy()
            w = table["Velocities_n:2"].to_numpy()

            U = np.sqrt(u ** 2 + v ** 2 + w ** 2).reshape(-1, 1) / reference_speed

            direction = (270 + np.degrees(np.arctan2(v, u))).reshape(-1, 1)

            label = float(file.stem)
            labels.append(label)

            if i == 0:
                speeds = U
                directions = direction
            else:
                speeds = np.concatenate((speeds, U), axis=1)
                directions = np.concatenate((directions, direction), axis=1)

        point_labels = ["X", "Y", "Z"]
        points.columns = point_labels

        directions = pd.DataFrame(data=directions, columns=labels).reset_index(drop=True)
        speeds = pd.DataFrame(data=speeds, columns=labels).reset_index(drop=True)

        return speeds, directions, points

    def set_external_building_assessment(self, external_building_assessment):
        '''
        Take an external building assessment and set it as the source.
        
        This allows us to get the run id's to download multi directional 
        results

        Parameters
        ----------
        external_building_assessment : external_building_assessment object
            The multidirectional external building assessment.

        Returns
        -------
        None.

        '''
        self.external_building_assessment = external_building_assessment

    def get_runs_from_external_building_assessment(self):
        '''
        Takes the set external building assessment and sets the Run ID's

        Returns
        -------
        None.

        '''
        self.project_id = self.external_building_assessment.project_id
        self.simulation_id = self.external_building_assessment.simulation_id
        self.run_ids = self.external_building_assessment.run_ids

        self.grids = self.external_building_assessment.grid

        self.test_conditions = self.external_building_assessment.test_conditions

        directions = self.test_conditions._atmospheric_boundary_layers.keys()
        for direction in directions:
            self.reference_speeds[direction] = self.test_conditions._atmospheric_boundary_layers[
                direction]._reference_speed

    def download_probe_plot_statistics(self, path=None, variables=["UMag (m/s)", "p (Pa)"],
                                       statistics=["AVG", "STDDEV"]):
        '''
        Download given variables and statistics from all probe plots

        Parameters
        ----------
        path : pathlib.Path, optional
            The path in which to save the dats. The default is None.
        variables : list of type string, optional
            The variables as written in the SimScale platform of those 
            you wish to keep. 
            
            The default is ["UMag (m/s)", "p (Pa)"].
            
        statistics : list of type string, optional
            The statistics as written in the SimScale platform of those 
            you wish to keep. 
            
            The default is ["AVG", "STDDEV"].

        Returns
        -------
        None.

        '''
        for key in self.grids.keys():
            for run in self.run_ids.keys():
                result = directional_result()
                result.get_run_from_multi_directional_result(self, run)
                result.query_results()
                if path == None:
                    result.download_result(category="PROBE_POINT_PLOT_STATISTICAL_DATA", name=key)
                else:
                    result.download_result(category="PROBE_POINT_PLOT_STATISTICAL_DATA", name=key, path=path)

                self.results[run] = result.download_dict

    def make_results_non_dimensional(self,
                                     grid,
                                     variables=["UMag"],
                                     statistics=["AVG"],
                                     path=pathlib.Path.cwd()
                                     ):
        '''
        Take a statistic from probe plots and make it non dimensional

        Parameters
        ----------
        grid : str
            The name of the grid to use.
        variables : list of type string, optional
            A list of the variables you wish to make non-dimensional. 
            
            The default is ["UMag"].
            
        statistics : list of type string, optional
            A list of the statistics you wish to make non-dimensional.
            
            The default is ["AVG"].
            
        path : pathlib.Path, optional
            A path to save the dimensionless results. 
            
            The default is pathlib.Path.cwd().
            
        Returns
        -------
        None.

        '''
        types = {
            "UMag": "speed",
            "Ux": "speed",
            "Uy": "speed",
            "Uz": "speed",
            "p": "pressure",
            "k_total": "tke",
            "k_resolved": "tke",
            "k_modeled": "tke"
        }

        result_dict = self.results

        # obtain no of points
        directions = list(result_dict.keys())
        temp_path = result_dict[directions[0]]["PROBE_POINT_PLOT_STATISTICAL_DATA"][grid][None]
        temp_group = probes_to_dataframe(temp_path)
        temp_group_keys = list(temp_group.keys())
        no_points = temp_group[temp_group_keys[0]].shape[0]

        empty_df = np.zeros([no_points, len(result_dict.keys())])

        result_tables = {}
        for var in variables:
            result_tables[var] = {}
            for statistic in statistics:
                result_tables[var][statistic] = {}
                dimensional_df = pd.DataFrame(data=empty_df, columns=directions)
                dimensionless_df = pd.DataFrame(data=empty_df, columns=directions)
                for key in result_dict.keys():
                    directional_path = result_dict[key]["PROBE_POINT_PLOT_STATISTICAL_DATA"][grid][None]
                    group = probes_to_dataframe(directional_path)
                    directional_result = group[var][statistic]

                    dimensional_df[key] = directional_result
                    dimensionless_df[key] = make_dimensionless(directional_result.copy(), types[var],
                                                               self.reference_speeds[key])
                    print(self.reference_speeds[key])

                dimensional_label = "dimensional_{}_{}.result".format(var, statistic)
                dimensional_path = path / dimensional_label
                dimensional_df.to_feather(dimensional_path)
                result_tables[var][statistic]["dimensional"] = dimensional_path

                dimensionless_label = "dimensionless_{}_{}.result".format(var, statistic)
                dimensionless_path = path / dimensionless_label
                dimensionless_df.to_feather(dimensionless_path)
                result_tables[var][statistic]["dimensionless"] = dimensionless_path
        self.exported_results_dict = result_tables

    def make_local_weibul_parameters(self):
        '''
        Takes the dimensionless speed and wind conditions, returns gamma
        
        The speed is the velocity magnitude, the wind conditions define 
        the meteorlogical corrector and the combination forms the gamma 
        term, the local corrector.
        
        Returns
        -------
        None.

        '''
        speed_up_factor_path = self.exported_results_dict["UMag"]["AVG"]["dimensionless"]
        speed_up_factor = pd.read_feather(speed_up_factor_path)

        meteo_correctors = self.weather_statistics.meteo_correctors

        directions = np.array(list(self.weather_statistics.meteo_correctors.keys()))
        points = speed_up_factor.index

        empty_array = np.ones(speed_up_factor.shape)
        local_gamma = pd.DataFrame(data=empty_array,
                                   columns=directions.astype(str),
                                   index=points)

        for direction in directions:
            local_gamma[str(direction)] = (
                    speed_up_factor[str(float(direction))]
                    * meteo_correctors[direction]
            )

        local_gamma.to_feather("gamma.result")

    def set_comfort_criteria(self, comfort_criteria):
        '''
        Takes the comfort criteria and sets it

        Parameters
        ----------
        comfort_criteria : comfort criteria object
            The object repressenting the comfort critria.

        Returns
        -------
        None.

        '''
        self.comfort_criteria = comfort_criteria

    def calculate_wind_comfort(self):
        '''
        Calulates and saves the local comfort criteria

        Returns
        -------
        None.

        '''
        gamma = pd.read_feather("gamma.result")
        weibull_parameters = self.weather_statistics.weibull_parameters
        comfort_criteria = self.comfort_criteria

        shape = weibull_parameters.loc["shape", :].values
        P = weibull_parameters.loc["probability", :].values
        scale = weibull_parameters.loc["scale", :].values

        speeds = []
        for i in range(0, len(comfort_criteria.comfort_dict)):
            speeds.append(comfort_criteria.comfort_dict[str(i)]["speed"])

        gamma_shape = gamma.shape
        X = gamma_shape[0]
        Y = gamma_shape[1]
        Z = len(comfort_criteria.comfort_dict)
        frequency_table = np.ones([X, Y, Z])
        iter_table = gamma.values

        # need to iterate gamma now
        it = np.nditer(iter_table, flags=['multi_index'], op_flags=['readwrite'])
        while not it.finished:
            freq = frequencies(speeds, params=[scale[it.multi_index[1]],
                                               shape[it.multi_index[1]],
                                               P[it.multi_index[1]],
                                               it[0]])

            frequency_table[it.multi_index[0],
            it.multi_index[1],
            :] = freq

            it.iternext()

        point_total = frequency_table.sum(axis=1)
        comfort_map = np.zeros(X)
        # return frequency_table
        for i in (list(range(0, len(comfort_criteria.comfort_dict)))):
            if comfort_criteria.comfort_dict[str(i)]["frequency"][0] == "less":

                criteria = (comfort_criteria.comfort_dict[str(i)]["frequency"][1]) / 100
                is_exceeding = point_total[:, i] > criteria
                print(np.nanmax(point_total[:, i]), np.nanmin(point_total[:, i]), criteria)
                comfort_map[is_exceeding] = i + 1

            elif comfort_criteria.comfort_dict[str(i)]["frequency"][0] == "greater":
                pass
                '''
                criteria = (comfort_criteria.comfort_dict[str(i)]["frequency"][1])/100
                is_exceeding = point_total[:, i] > criteria
                print(np.nanmax(point_total[:, i]), np.nanmin(point_total[:, i]), criteria)
                '''

        self.comfort_map = comfort_map

        df = pd.DataFrame(data=comfort_map, columns=["comfort"])
        df.to_feather("comfort_map_{}.result".format(self.comfort_criteria.name))

    def set_weather_statistics(self, weather_statistics):
        '''
        takes wether statistics and sets it for use in calulating comfort

        Parameters
        ----------
        weather_statistics : weather statistics object
            The weather statistics, i.e. processed to reveal probability 
            that a wind speed and direction bin might occure.

        Returns
        -------
        None.

        '''
        self.weather_statistics = weather_statistics

    def plot_cumulative_distributions(self):
        pass


class comfort_criteria():

    def __init__(self, name):
        self.name = name
        self.comfort_dict = {}

    def set_name(self, name):
        self.name = name

    def set_dict(self, _dict):
        self.comfort_dict = _dict


def make_dimensionless(df, _type, reference_velocity):
    if _type == "speed":
        return df / reference_velocity
    elif _type == "pressure":
        return df / (0.5 * 1.1965 * reference_velocity ** 2)
    elif _type == "tke":
        return df / reference_velocity ** 2
    else:
        raise Exception('Cannot make {} dimensionless.'.format(_type))


def frequencies(speeds, params):
    scale, shape, P, gamma = params
    bins = speeds / gamma
    probabilities = (weibull_min.sf(bins, shape, 0, scale)) * P
    return probabilities


def result_to_csv(path):
    data = pd.read_feather(path)
    save_path = path.with_suffix('.csv')
    data.to_csv(save_path)


def to_file(df, path):
    df.columns = df.columns.astype(str)
    df.to_feather(path)


def to_paraview(path, file):
    data = pd.read_feather(path / file).reset_index(drop=True)
    points = pd.read_feather(path / "points.result").reset_index(drop=True)

    df = pd.concat([points, data], axis=1, ignore_index=True)
    df.to_csv((path / file).with_suffix(".csv"))
