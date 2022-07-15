import json
import pathlib
import shutil
import zipfile
from itertools import groupby

import numpy as np
import pandas as pd
from scipy.stats import weibull_min
from sklearn.cluster import DBSCAN

import simscale_eba.SimulationCore as sc
import simscale_eba.TestConditions as tc
import simscale_eba.post_processing.NonDimensionalQuantities as nd
import simscale_eba.pwc_status as stat


class pedestrian_wind_comfort_setup():

    def __init__(self, credentials=None):
        
        self.api_client = None
        self.credentials = credentials
        self.api_key_header = None
        self.api_key = None

        self.project_api = None
        self.simulation_api = None
        self.mesh_operation_api = None
        self.run_api = None
        self.geometry_api = None
        self.geometry_import_api = None

        # SimScale ID's
        self.project_id = None
        self.simulation_id = None
        self.mesh_operation_id = None
        self.mesh_id = None
        self.run_id = None
        self.geometry_id = None

        self.geometry_id = None
        self.copper_id = None
        self.overmold_id = None

        self.simulation = None

        self.exposure_categories = []
        self.aerodynamic_roughnesses = []
        self.meteo_correctors = []
        self.directions = []
        self.wind_conditions = None

        self.wind_standard = None
        self.number_of_directions = None
        
        if self.credentials == None:
            sc.create_client(self)
        else:
            sc.get_keys_from_client(self)
            
        sc.create_api(self)

    def get_project(self, project):
        sc.find_project(self, project)

    def get_simulation(self, simulation):
        sc.find_simulation(self, simulation)
        self._get_simulation()
        self._get_wind_information()
        self._get_meteological_correctors()

    def _get_simulation(self):
        self.simulation = self.simulation_api.get_simulation(
            self.project_id, self.simulation_id)

    def get_example_mesh(self):
        spec = self.mesh_operation_api.get_mesh_operation_sdk_code(
            self.project_id, self.mesh_operation_id)

        return spec

    def _get_wind_information(self):
        self.exposure_categories = self.simulation.model.wind_conditions.wind_rose.exposure_categories
        self.wind_standard = self.simulation.model.wind_conditions.wind_rose.wind_engineering_standard
        self.number_of_directions = self.simulation.model.wind_conditions.wind_rose.num_directions
        self.directions = np.arange(start=0, stop=360, step=360 / self.number_of_directions)

        map_dict = {
            "EU": {"EC1": None, "EC2": 1, "EC3": 0.3, "EC4": 0.05, "EC5": 0.01, "EC6": 0.003},
            "AS_NZS": {"EC1": 2, "EC2": None, "EC3": 0.2, "EC4": 0.02, "EC5": 0.002, "EC6": None},
            "NEN8100": {"EC1": 2, "EC2": 1, "EC3": 0.5, "EC4": 0.25, "EC5": 0.03, "EC6": 0.0002},
            "LONDON": {"EC1": 1, "EC2": 0.5, "EC3": 0.3, "EC4": 0.05, "EC5": 0.01, "EC6": None},
        }

        standard_map = map_dict[self.wind_standard]

        aerodynamic_roughnesses = []
        for exposure_category in self.exposure_categories:
            aerodynamic_roughnesses.append(standard_map[exposure_category])

        self.aerodynamic_roughnesses = aerodynamic_roughnesses

    def _get_meteological_correctors(self):
        wind_conditions = tc.WindData()

        wind_conditions.set_atmospheric_boundary_layers(
            directions=np.arange(0, 360, 360 / self.number_of_directions).tolist(),
            surface_roughness_list=self.aerodynamic_roughnesses,
            reference_speeds=(10 * np.ones(self.number_of_directions)).tolist(),
            reference_heights=(10 * np.ones(self.number_of_directions)).tolist(),
            method_dict={'u': 'LOGLAW', 'tke': 'YGCJ', 'omega': 'YGCJ'},
            return_without_units=True
        )

        self.wind_conditions = wind_conditions
        self.meteo_correctors = wind_conditions.meteo_correctors

    def to_dict(self):
        output_dict = {}
        for direction, roughness, exposure in zip(self.directions,
                                                  self.aerodynamic_roughnesses,
                                                  self.exposure_categories):
            direction = str(direction)
            output_dict[direction] = {}
            output_dict[direction]["meteo_corrector"] = self.meteo_correctors[direction]
            output_dict[direction]["aerodynamic_roughness"] = roughness
            output_dict[direction]["exposure_categories"] = exposure

        return output_dict


class pedestrian_wind_comfort_results():

    def __init__(self, credentials=None, access_simscale=True):
        
        # The SimScale names
        self.project_name = None
        self.simulation_name = None
        self.run_name = None
        self.result_directory = None

        # SimScale ID's
        self.project_id = None
        self.simulation_id = None
        self.run_id = None
        self.geometry_id = None
        self.storage_id = None
        self.flow_domain_id = None
        self.wind_profile_id = {}

        # SimScale API's
        self.project_api = None
        self.simulation_api = None
        self.run_api = None
        self.geometry_api = None
        self.geometry_import_api = None
        self.storage_api = None

        # SimScale Authentication
        self.credentials = credentials
        self.api_client = None
        self.api_key_header = None
        self.api_key = None

        # Pedestrian Comfort Settings
        self.pedestrian_wind_comfort_setup = None
        self.number_of_directions = None
        self.number_of_points = None
        self.minimum_resolution = 0

        # Result Outputs
        self.url_dictionary_results = {}
        self.directional_csv_dict = {}
        self.dimensional_results = {}
        self.dimensionless_results = {}
        self.hourly_continuous_results = {}
        self.coordinates = None
        self.reduced_coordinates = None
        self.comfort_maps = {}

        # Weather objects
        self.weather_statistics = None
        self.comfort_criteria = None

        self.status = stat.simulation_status()
        
        if access_simscale:
            # Check and create API environment
            if self.credentials == None:
                sc.create_client(self)
                
            else:
                sc.get_keys_from_client(self)
            
            sc.create_api(self)

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

        setup = pedestrian_wind_comfort_setup(credentials=self.credentials)
        
        setup.get_project(project)
        setup.get_simulation(simulation)

        self.result_directory = pathlib.Path(path)

        self.project_name = project
        self.simulation_name = simulation
        self.run_name = run

        self.status.set_simulation(project, simulation, run)
        self.status.result_directory = self.result_directory

        self.pedestrian_wind_comfort_setup = setup
        
        self.project_id = setup.project_id
        self.simulation_id = setup.simulation_id

        self.project_api = setup.project_api
        self.run_api = setup.run_api
        '''
        self.api_client = setup.api_client
        self.api_key_header = setup.api_key_header
        self.api_key = setup.api_key
        '''
        sc.find_run(self, run)

        self.pull_run_results(output_folder=self.result_directory)

    def pull_run_results(self, 
                         output_folder=pathlib.Path.cwd(), 
                         cleanup=True):
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
        dict_ = self.url_dictionary_results

        csv_list = {}
        for key in dict_:
            #Only download new results if they are new or different
            if not self.status.check_simulation_status():
                case_file_path = self.download_average_direction_result(
                    direction=key, path=self.result_directory)
                
                sc.case_to_csv(
                    output.joinpath(key, case_file_path.name).as_posix(),
                    output.joinpath(f'{key}.csv').as_posix())

                csv_list[key] = output.joinpath(f'{key}.csv')
                #shutil.rmtree(output.joinpath(key).as_posix(), ignore_errors=True)

                self.status.update_download_path(
                    key, output.joinpath(f'{key}.csv').as_posix())
            else:
                if self.status.download_paths is None:
                    self.status.read_simulation_status()
                else:
                    csv_list[key] = pathlib.Path(
                        self.status.download_paths[key])
        
        #Just export the first file, caveate is that floor geom changes
        #per direction
        first_key = list(dict_.keys())[0]
        stl_input_file = output.joinpath(key, 
                                         self.download_average_direction_result(
                                             direction=first_key, 
                                             path=self.result_directory
                                        ).name).as_posix()
        
        #Only export the STL again if its new or different
        if not self.status.check_simulation_status():
            stl_dict = sc.case_to_stl(stl_input_file, output)
            self.status.output_stl_paths = stl_dict
        
        #After all processes remove original data
        if cleanup:
            for key in dict_:
                shutil.rmtree(output.joinpath(key).as_posix(), 
                              ignore_errors=True)
                
        self.directional_csv_dict = csv_list
        self.status.write_simulation_status(boolean=True)

        # number of directions should come from PWC setup
        self.number_of_directions = len(csv_list.keys())
        self._check_valid_comfort_plots()

    def _check_valid_comfort_plots(self):
        '''
        Checks number of points for all directions, exception if not all the same

        Raises
        ------
        Exception
            Occurs if comfort plots have different numbers of points, this
            is currently hard to handle, and in the scope of post processing
            will not be handled. 
            
            Later, we could simply check which points are pressent for all
            and keep only then. As a further step we culd do the same with
            a small tolerance for computational differences.

        '''
        no_points_list = []

        for key in self.directional_csv_dict.keys():
            df = pd.read_csv(self.directional_csv_dict[key])
            no_points = df.shape[0]
            no_points_list.append(no_points)

        is_equal = all_equal(no_points_list)

        if not is_equal:
            raise Exception("One or more directions, have comfort plots,"
                            "where the number of points are different."
                            "This usually happens if the wind tunnel"
                            "intersects the comfort plot. We cannot handle"
                            "thi currently")

    def _write_simulation_status(self, boolean):
        '''
        Take the PWC project, simulation and run, place them in a json file
        
        Here we are telling the result directory that the results stored
        belong to a certain run, and later, we can read it, and if the 
        run being requested is the same, we need not download again.

        '''
        json_dictionary = {
            "project_name": self.project_name,
            "simulation_name": self.simulation_name,
            "run_name": self.run_name,
            "is_result_downloaded": boolean}

        json_object = json.dumps(json_dictionary, indent=4)

        json_path = self.result_directory / "simulation.json"

        with open(json_path, "w") as outfile:
            outfile.write(json_object)

    def _check_simulation_status(self):
        json_path = self.result_directory / "simulation.json"

        signal = None
        try:

            with open(json_path, "r") as read_file:
                read_dict = json.load(read_file)

            match_project = self.project_name == read_dict["project_name"]
            match_simulation = self.simulation_name == read_dict["simulation_name"]
            match_run = self.run_name == read_dict["run_name"]
            is_downloaded = self.read_dict["is_result_downloaded"]

            if match_project and match_simulation and match_run and is_downloaded:
                print("Matched to already downloaded results")
                signal = True
            else:
                print("Results downloaded dont match, redownloading")
                signal = False
        except:
            print("No results exist, downloading")
            signal = False

        return signal

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
        simulation_run_api = self.run_api

        project_id = self.project_id
        simulation_id = self.simulation_id
        run_id = self.run_id

        results = simulation_run_api.get_simulation_run_results(
            project_id, simulation_id, run_id).embedded

        direction_dict = {}

        for result in results:
            if result.category == 'AVERAGED_SOLUTION':
                direction_dict[str(result.direction)] = result.download

        self.url_dictionary_results = direction_dict

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
        download_obj = self.url_dictionary_results[str(direction)]

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

    def _create_point_file(self):
        csv_file_key = list(self.directional_csv_dict.keys())[0]
        csv_file = self.directional_csv_dict[csv_file_key]

        table = pd.read_csv(pathlib.Path(csv_file.as_posix()))

        self.coordinates = table[["Points:0", "Points:1", "Points:2"]]

        columns = ["X", "Y", "Z"]

        self.coordinates.columns = columns

        path = self.directional_csv_dict[csv_file_key].with_name(
            "points").with_suffix(".feather")

        if self._check_is_reduce_needed():
            idx = self._reduce_resolution_idx()
        else:
            idx = self.coordinates.index

        
        self.reduced_coordinates = self.coordinates.loc[idx].reset_index()
        self.reduced_coordinates.to_feather(path)
        
        self.status.points_path = path.as_posix()
        self.status.write_simulation_status()

    def _create_dimensional_quantities(self, variables=['UMag', 'GEM']):
        '''
        Take csv files, return variables in standard format.
        
        Take the output .csv files from VTK, return a tabulated data
        set for each variable. The format is number of rows is the number
        of points, the number of columns is the number of directions.
        
        The data in the fields will be the variable, in dimensional form.
        
        The save formate is a feather file for fast writing and light 
        storage, with a custome extension of .feather. This should be 
        considered an  formate, the user should output a .csv for exporting.

        Parameters
        ----------
        variables : list[string], optional
            The variables you chose to return, current options are:
                
            - UMag
            - Ux
            - Uy
            - Uz
            - GEM
            - p
            - k_total
            - k_resolved
            - k_modeled
            
            The default is ['UMag', 'GEM'].

        Returns
        -------
        None.

        '''
        no_points = self._get_no_points()
        csv_list = self.directional_csv_dict

        result_dict = {}
        for variable in variables:
            result_dict[variable] = pd.DataFrame(
                np.zeros((no_points, self.number_of_directions)),
                columns=csv_list.keys())

        for i, direction in enumerate(csv_list):
            table = pd.read_csv(pathlib.Path(csv_list[direction]).as_posix())
            df = nd.csv_to_dimensionall_df(self, table, variables)
            for column in df.columns:
                result_dict[column][direction] = df[column]

        self._create_point_file()

        key = list(self.directional_csv_dict.keys())[0]
        for variable in variables:
            path = self.directional_csv_dict[key].with_name(
                "dimensional_{}".format(variable)).with_suffix(".feather")

            self.dimensional_results[variable] = path
            self.status.update_field_path(variable,
                                          path.as_posix(),
                                          is_dimensional=True)

            if self._check_is_reduce_needed():
                idx = self._reduce_resolution_idx()
            else:
                idx = result_dict[variable].index

            result_dict[variable].loc[idx].reset_index().to_feather(path)
            
        self.status.write_simulation_status()

    def _create_dimensionless_quantities(self, variables=['UMag', 'GEM']):
        '''
        Take csv files, return variables in standard format.
        
        Take the output .csv files from VTK, return a tabulated data
        set for each variable. The format is number of rows is the number
        of points, the number of columns is the number of directions.
        
        The data in the fields will be the variable, in dimensional form.
        
        The save formate is a feather file for fast writing and light 
        storage, with a custome extension of .feather. This should be 
        considered an  formate, the user should output a .csv for exporting.

        Parameters
        ----------
        variables : list[string], optional
            The variables you chose to return, current options are:
                
            - UMag
            - Ux
            - Uy
            - Uz
            - GEM
            - p
            - k_total
            - k_resolved
            - k_modeled
            
            The default is ['UMag', 'GEM'].

        Returns
        -------
        None.

        '''
        no_points = self._get_no_points()
        csv_list = self.directional_csv_dict

        result_dict = {}
        for variable in variables:
            result_dict[variable] = pd.DataFrame(
                np.zeros((no_points, self.number_of_directions)),
                columns=csv_list.keys())

        for i, direction in enumerate(csv_list):
            table = pd.read_csv(pathlib.Path(csv_list[direction]).as_posix())
            df = nd.csv_to_dimensionless_df(self, table, variables, direction)
            for column in df.columns:
                result_dict[column][direction] = df[column]

        self._create_point_file()

        key = list(self.directional_csv_dict.keys())[0]
        for variable in variables:
            path = self.directional_csv_dict[key].with_name(
                "dimensionless_{}".format(variable)).with_suffix(".feather")

            self.dimensionless_results[variable] = path
            self.status.update_field_path(variable,
                                          path.as_posix(),
                                          is_dimensional=False)

            if self._check_is_reduce_needed():
                idx = self._reduce_resolution_idx()
            else:
                idx = result_dict[variable].index

            result_dict[variable].loc[idx].reset_index().to_feather(path)

        self.status.write_simulation_status()
        
    def _create_hourly_continuous_windspeed(self, output_file='feather'):
        '''
        Take houly continuous (HC) and dimensionless speed, return HC spatial.

        use hourly continuous object to pass the meteological speeds and
        directions.
        
        Use _create_dimensionless_quantities()
        '''
        
        epw_directions = self.weather_statistics.hourly_continuous._original_df['direction'].to_numpy().astype(float)
        
        epw_speeds = self.weather_statistics.hourly_continuous._original_df['speed'].to_numpy().astype(float)
        
        field_paths = self.status.field_paths["dimensionless_UMag"]
        
        def get_speeds(direction, reference_speed, keys):
            '''
            Take direction, speed and a clustered map key, return speed
            
            Based upon meteo data, return a wind speed result from the
            closed solved wind direction and scaled to the defined speed.
            
            A PWC result here may have multiple maps, so we need to 
            specify which also.

            Parameters
            ----------
            direction : float
                Wind direction as a float in compass angles.
            reference_speed : float
                The wind speed at the meteological station.
            keys : str
                The comfort map.

            '''
            
            field_path = pathlib.Path(field_paths[keys])
            
            rounded_direction = round_direction(field_path, direction)
            
            field = pd.read_feather(field_path)[str(rounded_direction)]
            speed = (field * reference_speed).values
            
            return np.reshape(speed, (-1, 1))
        
        mySpeedFunc = np.frompyfunc(get_speeds, 3, 1)
        
        
        #Iterate the clustered maps
        names = []
        for key in field_paths.keys():
            keys = np.repeat(key, len(epw_directions))
            
            hc_speeds = np.concatenate(mySpeedFunc(epw_directions, epw_speeds, keys), axis=1)
            
            self.hourly_continuous_results[key] = hc_speeds
            
            #we should really also add this to status, including, period.
            field_path = pathlib.Path(field_paths[key])
            
            field = pd.read_feather(field_path)
            index = field.index
            
            df = pd.DataFrame(hc_speeds, index=index)
            df.columns = df.columns.astype("string")
            self.hourly_continuous_results[key] = df
            
            if output_file =='feather':
                speed_matric_path = self.result_directory / "speed_matrix_{}.feather".format(key)
                df.reset_index().to_feather(speed_matric_path)
            else: 
                speed_matric_path = self.result_directory / "speed_matrix_{}.csv".format(key)
                df.reset_index(drop=True).to_csv(speed_matric_path, 
                                                 header=False, index=False)
            
            names.append(speed_matric_path.stem)
            
        return names

    def _get_no_points(self):
        '''
        Takes a csv and returns the number of points in the comfort map

        Returns
        -------
        int
            An int, representing the number of points in the comfort plot.

        '''
        key = list(self.directional_csv_dict.keys())[0]
        df = pd.read_csv(pathlib.Path(self.directional_csv_dict[key]).as_posix())
        self.number_of_points = df.shape[0]
        return self.number_of_points

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
        variables = ['UMag']
        self._create_dimensionless_quantities(variables=variables)
        self._create_point_file()

        variable_results = {}

        for variable in variables:

            result_file = self.dimensionless_results[variable]

            gamma = pd.read_feather(result_file)
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

            for i in (list(range(0, len(comfort_criteria.comfort_dict)))):
                if comfort_criteria.comfort_dict[str(i)]["frequency"][0] == "less":

                    criteria = (comfort_criteria.comfort_dict[str(i)]["frequency"][1]) / 100
                    is_exceeding = point_total[:, i] > criteria
                    print(np.nanmax(point_total[:, i]),
                          np.nanmin(point_total[:, i]),
                          criteria)
                    comfort_map[is_exceeding] = i + 1

                elif comfort_criteria.comfort_dict[str(i)]["frequency"][0] == "greater":
                    pass

            variable_results[variable] = comfort_map

        combined_array = np.zeros((X, len(variables)))
        for i in range(0, len(variables)):
            combined_array[:, i] = variable_results[variables[i]]

        worst_case = combined_array.max(axis=0)

        self.comfort_maps = {"worst_case": worst_case}

        for variable in variables:
            self.comfort_maps[variable] = variable_results[variable]

        for key in self.comfort_maps.keys():
            df = pd.DataFrame(
                data=self.comfort_maps[key],
                columns=["comfort"])

            df.to_feather("comfort_map_{}_{}.feather".format(
                key, self.comfort_criteria.name))

    def set_resolution(self, resolution):
        if type(resolution) != float:
            raise Exception("resolution should be a float in meters")
        self.minimum_resolution = resolution
        self.status.minimum_resolution = resolution

    def _check_is_reduce_needed(self):
        if self.minimum_resolution > 0:
            return True
        else:
            return False

    def _reduce_resolution_idx(self):
        '''
        Take a fine point cloud, return a coarser one.

        Parameters
        ----------
        points : dataframe
            A dataframe of point locations with 3 columns, X, Y and Z, the 
            number of rows is the number of points.
        resolution : int or float
            int or float, optional
            an integer or float that represents the desired resolution in 
            meters, for example, if we wanted an output sensor grid no 
            finner than 5m then we can input 5.

        Returns
        -------
        grid_candidate_center_id : list
            The ID's of the points in the original points list to KEEP, 
            i.e. if we reduce the resolution from 0.5m to 5m, which points 
            closest represent an evenly spaced grid with spaces of 5m, the 
            resulting grid will not be structured.

        '''
        points = self.coordinates.to_numpy()

        voxel_size = self.minimum_resolution

        non_empty_voxel_keys, inverse, nb_pts_per_voxel = np.unique(
            ((points - np.min(points, axis=0)) // voxel_size).astype(int),
            axis=0,
            return_inverse=True,
            return_counts=True)

        idx_pts_vox_sorted = np.argsort(inverse)

        voxel_grid = {}
        ids_grid = {}

        grid_barycenter = []
        grid_candidate_center = []
        grid_candidate_center_id = []
        last_seen = 0

        for idx, vox in enumerate(non_empty_voxel_keys):
            voxel_grid[tuple(vox)] = points[
                idx_pts_vox_sorted[last_seen:last_seen + nb_pts_per_voxel[idx]]]

            ids_grid[tuple(vox)] = idx_pts_vox_sorted[
                                   last_seen:last_seen + nb_pts_per_voxel[idx]]

            # The geometric centre of a grid space
            grid_barycenter.append(np.mean(voxel_grid[tuple(vox)], axis=0))

            # The point closest to the centre of a grid space
            grid_candidate_center.append(
                voxel_grid[tuple(vox)][np.linalg.norm(voxel_grid[tuple(vox)]
                                                      - np.mean(voxel_grid[tuple(vox)], axis=0), axis=1).argmin()])

            # The ID of the same point
            grid_candidate_center_id.append(
                ids_grid[tuple(vox)][np.linalg.norm(voxel_grid[tuple(vox)]
                                                    - np.mean(voxel_grid[tuple(vox)], axis=0), axis=1).argmin()])

            last_seen += nb_pts_per_voxel[idx]
            
        
        return grid_candidate_center_id

    def _cluster_points(self):
        '''
        Take point ordinates, and split results into seperate point clouds
        
        This uses a clustering analysis to seperate the points list into
        seperate point clouds that can represent different comfort plots.
        
        Returns
        -------
        None.

        '''
        points_path = self.status.points_path
        points_directory = pathlib.Path(points_path).parent

        points = pd.read_feather(points_path)
        points = points.set_index("index", drop=True)

        clustering = DBSCAN(eps=self.minimum_resolution * 1.5, min_samples=5).fit(points.values)

        cluster_index = pd.DataFrame(clustering.labels_, columns=["cluster"])
        cluster_index_groups = list(cluster_index.groupby("cluster"))

        cluster_index_lists = []
        points_path_dict = {}
        for group in cluster_index_groups:
            cluster_index_lists.append(group[1].index)

            cluster_points = points.iloc[group[1].index]
            cluster_points = cluster_points.reset_index()

            point_cluster_path = points_directory / "points{}.feather".format(group[0])

            cluster_points.to_feather(point_cluster_path)
            points_path_dict[str(group[0])] = point_cluster_path.as_posix()

        self.status.points_path = points_path_dict
        self.status.write_simulation_status()

        return cluster_index_groups

    def _cluster_fields(self, cluster_index_groups):
        field_paths = self.status.field_paths

        for key in field_paths.keys():
            field_path_dict = {}
            for group in cluster_index_groups:
                field_path = pathlib.Path(field_paths[key])

                field = pd.read_feather(field_path)
                field = field.set_index("index", drop=True)

                field_cluster_path = (field_path.parent
                                      / (field_path.stem
                                         + str(group[0])
                                         + field_path.suffix))

                cluster_field = field.iloc[group[1].index]
                cluster_field = cluster_field.reset_index()

                cluster_field.to_feather(field_cluster_path)
                field_path_dict[str(group[0])] = field_cluster_path.as_posix()

            field_paths[key] = field_path_dict

        self.status.field_paths = field_paths
        self.status.write_simulation_status()

    def cluster_outputs(self):
        cluster_index_groups = self._cluster_points()
        self._cluster_fields(cluster_index_groups)


class comfort_criteria():

    def __init__(self, name):
        self.name = name
        self.comfort_dict = {}

    def set_name(self, name):
        self.name = name

    def set_dict(self, _dict):
        self.comfort_dict = _dict


def frequencies(speeds, params):
    scale, shape, P, gamma = params
    bins = speeds / gamma
    probabilities = (weibull_min.sf(bins, shape, 0, scale)) * P
    return probabilities


def all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def to_paraview(path, file):
    data = pd.read_feather(path / file).reset_index(drop=True)
    points = pd.read_feather(path / "points.feather").reset_index(drop=True)

    columns = list(points.columns) + list(data.columns)

    df = pd.concat([points, data], axis=1, ignore_index=True)
    df.columns = columns
    df.to_csv((path / file).with_suffix(".csv"))


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
            if direction < interval[i] or direction >= interval[-1]:
                direction_bin = i
                break
        else:
            if direction >= interval[i - 1] and direction < interval[i]:
                direction_bin = i
                break

    rounded_direction = columns[direction_bin]

    return rounded_direction


def reduce_resolution(points, resolution):
    '''
    Take a fine point cloud, return a coarser one.

    Parameters
    ----------
    points : dataframe
        A dataframe of point locations with 3 columns, X, Y and Z, the 
        number of rows is the number of points.
    resolution : int or float
        int or float, optional
        an integer or float that represents the desired resolution in 
        meters, for example, if we wanted an output sensor grid no 
        finner than 5m then we can input 5.

    Returns
    -------
    grid_candidate_center_id : list
        The ID's of the points in the original points list to KEEP, 
        i.e. if we reduce the resolution from 0.5m to 5m, which points 
        closest represent an evenly spaced grid with spaces of 5m, the 
        resulting grid will not be structured.

    '''
    points = points.to_numpy()

    voxel_size = resolution

    non_empty_voxel_keys, inverse, nb_pts_per_voxel = np.unique(
        ((points - np.min(points, axis=0)) // voxel_size).astype(int),
        axis=0,
        return_inverse=True,
        return_counts=True)

    idx_pts_vox_sorted = np.argsort(inverse)

    voxel_grid = {}
    ids_grid = {}

    grid_barycenter = []
    grid_candidate_center = []
    grid_candidate_center_id = []
    last_seen = 0

    for idx, vox in enumerate(non_empty_voxel_keys):
        voxel_grid[tuple(vox)] = points[
            idx_pts_vox_sorted[last_seen:last_seen + nb_pts_per_voxel[idx]]]

        ids_grid[tuple(vox)] = idx_pts_vox_sorted[
                               last_seen:last_seen + nb_pts_per_voxel[idx]]

        # The geometric centre of a grid space
        grid_barycenter.append(np.mean(voxel_grid[tuple(vox)], axis=0))

        # The point closest to the centre of a grid space
        grid_candidate_center.append(
            voxel_grid[tuple(vox)][np.linalg.norm(voxel_grid[tuple(vox)]
                                                  - np.mean(voxel_grid[tuple(vox)], axis=0), axis=1).argmin()])

        # The ID of the same point
        grid_candidate_center_id.append(
            ids_grid[tuple(vox)][np.linalg.norm(voxel_grid[tuple(vox)]
                                                - np.mean(voxel_grid[tuple(vox)], axis=0), axis=1).argmin()])

        last_seen += nb_pts_per_voxel[idx]

    return grid_candidate_center_id


def reduce_field(data, idx):
    '''
    Take dataframe and ID's, return a datafram with only data at ID's.

    Parameters
    ----------
    data : dataframe
        A dataframe or series of original data.
    idx : list
        A list of ID's we want to keep.

    Returns
    -------
    data_of_reduced_resolution : dataframe

    '''
    data_of_reduced_resolution = data.iloc[idx]
    return data_of_reduced_resolution


class dimensionaliser():

    def __init__(self, status):
        self.status = status

    def return_dimensional_speed(self, direction, reference_speed):
        path = pathlib.Path(
            self.status.field_paths["dimensionless_UMag"])

        df = pd.read_feather(path)

        direction = round_direction(path, direction)

        speed = df[str(float(direction))] * float(reference_speed)

        return speed

    def return_points(self):
        path = pathlib.Path(
            self.status.points_path)

        df = pd.read_feather(path)

        return df
