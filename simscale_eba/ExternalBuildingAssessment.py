import pathlib
import time

import simscale_sdk as sim
import pandas as pd

import simscale_eba.SimulationCore as sc


class PedestrianComfort():

    def __init__(self, name='PWC', 
                 server='prod',
                 credentials=None, 
                 run_number=1):
        self.name = name
        
        self.project = None
        self.simulation = None
        self.runs = {}
        self.geometry = None
        self.flow_domain = None
        self.simulation_spec = None
        self.simulation_model = None

        self.building_geom = None
        self.geometry_path = None
        self.dwt_geometry_paths = {}
        self.geometry_name = None

        self.project_id = None
        self.simulation_id = None
        self.run_ids = {}
        self.geometry_id = None
        self.directional_geometry_id = {}
        self.storage_id = None
        self.flow_domain_id = None
        self.direction_flow_domain_ids = {}
        self.wind_profile_id = {}
        
        # SimScale API's
        self.project_api = None
        self.simulation_api = None
        self.run_api = None
        self.geometry_api = None
        self.geometry_import_api = None
        self.storage_api = None
        self.table_import_api = None

        self.vertical_slice = None
        self.grid = {}
        self.plot_ids = []
        self.run_number = run_number
        
        # SimScale Authentication
        self.credentials = credentials
        self.api_client = None
        self.api_key_header = None
        self.api_key = None

        self.test_conditions = None
        self.region_of_interest = None
        self.number_of_fluid_passes = 3
        self.advanced_modelling = None
        self.surface_roughness = 0
        self.topological_reference = None
        
        self.mesh_fineness = "COARSE" 

        # Check and create API environment
        if self.credentials == None:
            sc.create_client(self, server=server)
            
        else:
            sc.get_keys_from_client(self)
        
        sc.create_api(self)

    def create_new_project(self, name, description):
        '''
        Take a name and description and create a new workbench project

        Parameters
        ----------
        name : str
            A string with the exact name for the new project.
            
        description : str
            A string with the exact description for the new project.

        Returns
        -------
        None.

        '''
        try:
            sc.find_project(self, name)
            print("Cannot create project with the same name, using existing project")
        except:
            project = sim.Project(name=name, description=description)
            project = self.project_api.create_project(project)
            self.project_id = project.project_id
            self.project = name

    def set_geometry(self, geometry_path):
        '''
        Set the path for a geometry to be uploaded

        Parameters
        ----------
        geometry_path : pathlib.Path
            A path to the geometry file.

        Returns
        -------
        None.

        '''
        self.geometry_path = geometry_path
        
    def set_dwt_geometry(self, _dir, dwt, geometry_path=None):
        
        def file_compress(inp_file_names, out_zip_file):
            """
            function : file_compress
            args : inp_file_names : list of filenames to be zipped
            out_zip_file : output zip file
            return : none
            assumption : Input file paths and this code is in same directory.
            """
            
            '''
            https://www.tutorialspoint.com/how-to-compress-files-with-zipfile-module-in-python
            '''
            import zipfile
            # Select the compression mode ZIP_DEFLATED for compression
            # or zipfile.ZIP_STORED to just store the file
            compression = zipfile.ZIP_DEFLATED
            print(f" *** Input File name passed for zipping - {inp_file_names}")
            
            # create the zip file first parameter path/name, second mode
            print(f' *** out_zip_file is - {out_zip_file}')
            zf = zipfile.ZipFile(out_zip_file, mode="w")
            
            try:
                for file_to_write in inp_file_names:
                    # Add file to the zip file
                    # first parameter file to zip, second filename in zip
                    print(f' *** Processing file {file_to_write}')
                    zf.write(file_to_write, arcname=file_to_write.name, compress_type=compression)
            
            except FileNotFoundError as e:
                print(f' *** Exception occurred during zip process - {e}')
            finally:
                # Don't forget to close the file!
                zf.close()
        
        if geometry_path != None:
            import zipfile
            with zipfile.ZipFile(geometry_path, 'r') as zip_ref:
                zip_ref.extractall(dwt.path)
                
        path_list = dwt.path.glob('*.stl')
        
        export_path = dwt.path / 'export.zip'
        
        self.dwt_geometry_paths[_dir] = file_compress(path_list, export_path) 
        

    def upload_geometry(self, name, path=None, units="m", _format="STL", facet_split=False):
        '''
        Upload a geometry to the SimScale platform to a preassigned project.
        
        This is a modified version of the upload coad from the API examples.

        Parameters
        ----------
        name : str
            The name given to the geometry.
        path : pathlib.Path, optional
            The path to a geometry to upload. 
            
            The default is predefined.
            
        units : str, optional
            the unit in which to upload the geometry to SimScale.
            
            The default is "m".
            
        _format : str, optional
            The file format. 
            
            The default is "STL".
            
        facet_split : bool, optional
            Decide on weather to split facet geometry (such as .stl file 
            types). We prefer not to do this for API use.
            
            The default is False.

        Raises
        ------
        TimeoutError
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        self.geometry_name = name
        try:
            sc.find_geometry(self, name)
            print("Cannot upload geometry with the same name, using existing geometry")
        except:
            if path is not None:
                self.set_geometry(path)

            storage = self.storage_api.create_storage()
            with open(self.geometry_path, 'rb') as file:
                self.api_client.rest_client.PUT(url=storage.url, headers={'Content-Type': 'application/octet-stream'},
                                                body=file.read())
            self.storage_id = storage.storage_id

            geometry_import = sim.GeometryImportRequest(
                name=name,
                location=sim.GeometryImportRequestLocation(self.storage_id),
                format=_format,
                input_unit=units,
                options=sim.GeometryImportRequestOptions(facet_split=facet_split, sewing=False, improve=True,
                                                         optimize_for_lbm_solver=True),
            )

            geometry_import = self.geometry_import_api.import_geometry(self.project_id, geometry_import)
            geometry_import_id = geometry_import.geometry_import_id

            geometry_import_start = time.time()
            while geometry_import.status not in ('FINISHED', 'CANCELED', 'FAILED'):
                # adjust timeout for larger geometries
                if time.time() > geometry_import_start + 900:
                    raise TimeoutError()
                time.sleep(10)
                geometry_import = self.geometry_import_api.get_geometry_import(self.project_id, geometry_import_id)
                print(f'Geometry import status: {geometry_import.status}')
            self.geometry_id = geometry_import.geometry_id
            
    def _upload_dwt_geometry(self, 
                             name, 
                             dwt_tc=None, 
                             path=None, 
                             units="m", _format="STL", facet_split=False):
        '''
        Upload a geometry to the SimScale platform to a preassigned project.
        
        This is a modified version of the upload coad from the API examples.

        Parameters
        ----------
        name : str
            The name given to the geometry.
        path : pathlib.Path, optional
            The path to a geometry to upload. 
            
            The default is predefined.
            
        units : str, optional
            the unit in which to upload the geometry to SimScale.
            
            The default is "m".
            
        _format : str, optional
            The file format. 
            
            The default is "STL".
            
        facet_split : bool, optional
            Decide on weather to split facet geometry (such as .stl file 
            types). We prefer not to do this for API use.
            
            The default is False.

        Raises
        ------
        TimeoutError
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        for _dir in dwt_tc.dwt_objects:
            #dwt_path = dwt_tc.dwt_objects[_dir].path
            name = name + str(_dir)
            try:
                sc.find_geometry(self, name)
                print("Cannot upload geometry with the same name, using existing geometry")
            except:
                self.set_dwt_geometry(_dir, dwt_tc.dwt_objects[_dir], path)
    
                storage = self.storage_api.create_storage()
                with open(self.dwt_geometry_paths[_dir], 'rb') as file:
                    self.api_client.rest_client.PUT(url=storage.url, headers={'Content-Type': 'application/octet-stream'},
                                                    body=file.read())
                self.storage_id = storage.storage_id
    
                geometry_import = sim.GeometryImportRequest(
                    name=name,
                    location=sim.GeometryImportRequestLocation(self.storage_id),
                    format=_format,
                    input_unit=units,
                    options=sim.GeometryImportRequestOptions(facet_split=facet_split, sewing=False, improve=True,
                                                             optimize_for_lbm_solver=True),
                )
    
                geometry_import = self.geometry_import_api.import_geometry(self.project_id, geometry_import)
                geometry_import_id = geometry_import.geometry_import_id
    
                geometry_import_start = time.time()
                while geometry_import.status not in ('FINISHED', 'CANCELED', 'FAILED'):
                    # adjust timeout for larger geometries
                    if time.time() > geometry_import_start + 900:
                        raise TimeoutError()
                    time.sleep(10)
                    geometry_import = self.geometry_import_api.get_geometry_import(self.project_id, geometry_import_id)
                    print(f'Geometry import status: {geometry_import.status}')
                self.directional_geometry_id[_dir] = geometry_import.geometry_id

    def set_region_of_interest(self, roi):
        self.region_of_interest = roi
        
        if self.test_conditions != None:
            for direction in self.test_conditions.directions:
                self._create_wind_tunnel(direction=direction)
        
    def set_wind_conditions(self, WindData):
        '''
        Set a wind condition to the analysis
        

        Parameters
        ----------
        WindData : WindCondition object
            A wind condition is a collection of ABL profiles for a collection
            of directions.

        Returns
        -------
        None.

        '''
        self.test_conditions = WindData
        
        self._upload_abl_profiles()
        
        if self.region_of_interest != None:
            for direction in WindData.directions:
                self._create_wind_tunnel(direction=str(direction))
    
    def _upload_abl_profiles(self):
        '''
        Upload all defined directional abl profiles to the simscale platform
        
        This is mainly for internal use
        
        Returns
        -------
        None.
    
        '''
        for key in self.test_conditions._atmospheric_boundary_layers:
            abl = self.test_conditions._atmospheric_boundary_layers[key]
            _list = ["u", "tke", "omega"]
            path = pathlib.Path("{}.csv".format(key))
            abl.to_csv(path, _list)
            print(path)
            inlet_profile_csv_storage = self.storage_api.create_storage()
            with open(path, 'rb') as file:
                self.api_client.rest_client.PUT(url=inlet_profile_csv_storage.url,
                                                headers={'Content-Type': 'application/octet-stream'},
                                                body=file.read())
    
            inlet_profile_csv_storage_id = inlet_profile_csv_storage.storage_id
            inlet_profile_table_import = sim.TableImportRequest(
                location=sim.TableImportRequestLocation(inlet_profile_csv_storage_id))
            inlet_profile_table_import_response = self.table_import_api.import_table(self.project_id,
                                                                                     inlet_profile_table_import)
            inlet_profile_table_id = inlet_profile_table_import_response.table_id
    
            self.wind_profile_id[key] = inlet_profile_table_id
    
    def _init_model(self):
        
        model = model_obj()
        self.simulation_model = model.model
        
    def _init_default_wind_tunnel(self):
        default_direction = list(self.direction_flow_domain_ids.keys())[0]
        self._set_wind_tunnel(default_direction)
        
    def _set_wind_tunnel(self, direction):
        self.simulation_model.bounding_box_uuid = self.direction_flow_domain_ids[direction]
        
        self.simulation_model.\
        mesh_settings_new.\
        reference_length_computation = sim.ManualReferenceLength(
            value=sim.DimensionalTime(
                value=self.region_of_interest._radius*2, unit="m")
            )
        
        self._create_vertical_slice()
        
    def _get_simulation_length(self, number_of_fluid_passes=3, direction=None):
        if direction == None:
            direction = list(self.direction_flow_domain_ids.keys())[0]
        wt_length = self.region_of_interest._wt_length
        
        reference_speed = self.test_conditions.reference_speeds[str(direction)].m
        
        time = (wt_length/reference_speed)*number_of_fluid_passes
        
        return time
    
    def _set_simulation_length(self, number_of_fluid_passes):
        
        self.simulation_model.\
            simulation_control.\
            end_time.\
            value = self._get_simulation_length(number_of_fluid_passes=\
                                                    number_of_fluid_passes)
        
    def _init_default_wind_abl(self):
        '''
        Sets the first region directions abl
        
        Returns
        -------
        None.

        '''
        direction = list(self.direction_flow_domain_ids.keys())[0]
            
        self._set_abl_table(str(direction))
             
    def _set_abl_table(self, direction:str):
        '''
        Takes a direction, sets it in the boundary condition xmin

        Returns
        -------
        None.

        '''
        #Set velocity
        self.simulation_model.\
             flow_domain_boundaries.\
             xmin.\
             velocity.\
             value.value.\
             table_id = self.wind_profile_id[direction]
             
        self.simulation_model.\
             flow_domain_boundaries.\
             xmin.\
             velocity.\
             value.value.\
             result_index = [2]
        
        #Set TKE
        self.simulation_model.\
             flow_domain_boundaries.\
             xmin.\
             turbulence_intensity.\
             value.value.\
             table_id = self.wind_profile_id[direction]
             
        self.simulation_model.\
             flow_domain_boundaries.\
             xmin.\
             turbulence_intensity.\
             value.value.\
             result_index = [3]
        
        #Set Omega
        self.simulation_model.\
             flow_domain_boundaries.\
             xmin.\
             dissipation_type.\
             value.value.\
             table_id = self.wind_profile_id[direction]
             
        self.simulation_model.\
             flow_domain_boundaries.\
             xmin.\
             dissipation_type.\
             value.value.\
             result_index = [4]
        
    def _create_vertical_slice(self):
        '''
        Creates a vertical slice for assessing the ABL accross the domain

        Returns
        -------
        None.

        '''
        X = self.region_of_interest._centre[0]
        Y = self.region_of_interest._centre[1]
        Z = self.region_of_interest._ground_height

        reference_point = sim.DimensionalVectorLength(value=sim.DecimalVector(x=X, y=Y, z=Z), unit='m')
        normal = sim.DimensionalVectorLength(value=sim.DecimalVector(x=0, y=1, z=0), unit='m')
        geometry_primitive = sim.LocalHalfSpace(name="Vertical Slice",
                                                reference_point=reference_point,
                                                normal=normal,
                                                orientation_reference="FLOW_DOMAIN"
                                                )

        _slice = self.simulation_api.create_geometry_primitive(self.project_id, geometry_primitive)
        
        self.simulation_model.\
             result_control.\
             statistical_averaging_result_control.\
             geometry_primitive_uuids = [_slice.geometry_primitive_id]
             
        self.simulation_model.\
             result_control.\
             snapshot_result_control.\
             geometry_primitive_uuids = [_slice.geometry_primitive_id]
             
        self.simulation_model.\
             result_control.\
             transient_result_control.\
             geometry_primitive_uuids = [_slice.geometry_primitive_id]
             
        self.vertical_slice = _slice.geometry_primitive_id
    
    def _create_default_spec(self, 
                             fineness = 'COARSE', 
                             number_of_fluid_passes=3,
                             ):
        self._init_model()
        self._init_default_wind_tunnel()
        self._init_default_wind_abl()
        if self.building_geom == None:
            self._get_geometry_map()
        self._set_buildings_as_mesh_entities()
        self._set_simulation_length(number_of_fluid_passes=number_of_fluid_passes)
        self._set_probe_plots()
        
        self.set_mesh_fineness(fineness)
        self.simulation_spec = sim.SimulationSpec(name=self.name, 
                                                  geometry_id=self.geometry_id, 
                                                  model=self.simulation_model)        
    
    def set_manual_reynolds_scaling(self, reynolds_scale=1):
        
        self.simulation_model.\
             mesh_settings_new.\
             reynolds_scaling_type = sim.ManualReynoldsScaling(type='MANUAL_REYNOLDS_SCALING', 
                                                               reynolds_scaling_factor=reynolds_scale)
        
        
    
    def create_default_simulation(self, fineness = 'COARSE', number_of_fluid_passes=3):
        
        self._create_default_spec(fineness=fineness,
                                  number_of_fluid_passes=number_of_fluid_passes)
        
        self.simulation = self.simulation_api.create_simulation(self.project_id, self.simulation_spec)
        self.simulation_id = self.simulation.simulation_id
    
    def create_simulation(self, fineness='COARSE', number_of_fluid_passes=3):
        try:
            sc.find_simulation(self, self.name)
            print("Cannot create simulation with the same name, using existing simulation")
            self._create_default_spec(fineness=fineness,
                                      number_of_fluid_passes=number_of_fluid_passes)
            self._update_spec(self.simulation_spec)
        except:
            self.create_default_simulation(fineness=fineness,
                                           number_of_fluid_passes=number_of_fluid_passes)

    def _create_wind_tunnel(self, direction=0):

        external_flow_domain = sim.RotatableCartesianBox(
            name='External Flow Domain',
            max=sim.DimensionalVectorLength(value=sim.DecimalVector(
                x=self.region_of_interest._wt_maximum_point[0],
                y=self.region_of_interest._wt_maximum_point[1],
                z=self.region_of_interest._wt_maximum_point[2]),
                unit='m'),

            min=sim.DimensionalVectorLength(value=sim.DecimalVector(
                x=self.region_of_interest._wt_minimum_point[0],
                y=self.region_of_interest._wt_minimum_point[1],
                z=self.region_of_interest._wt_minimum_point[2]),
                unit='m'),

            rotation_point=sim.DimensionalVectorLength(
                value=sim.DecimalVector(x=self.region_of_interest._centre[0],
                                        y=self.region_of_interest._centre[1],
                                        z=self.region_of_interest._ground_height),
                unit='m'
            ),

            rotation_angles=sim.DimensionalVectorAngle(value=sim.DecimalVector(
                x=0, y=0, z=-90 - float(direction)),
                unit='°'),
        )
        self.flow_domain = external_flow_domain
            
        self.direction_flow_domain_ids[
            direction] = self.simulation_api.create_geometry_primitive(
                self.project_id,
                external_flow_domain).geometry_primitive_id
    
    def _get_geometry_map(self, names=['BUILDING_OF_INTEREST', 'CONTEXT']):
        '''
        get the map of geometry from a CAD.
        
        Currently this only supports single layer STL files, but will 
        be expanded to take many layers conforming to a naming convention.

        Returns
        -------
        None.

        '''
        project_id = self.project_id
        geometry_id = self.geometry_id
        maps = self.geometry_api.get_geometry_mappings(project_id, geometry_id, _class='body')
        
        if len(maps.embedded) == 1:
            mesh_geom = maps.embedded[0]
            self.building_geom = [mesh_geom.name]
        else:
            entities = []
            for entity in maps.embedded:
                for attribute in entity.originate_from:
                    if attribute.body in names:
                        entities.append(entity.name)
                        
            self.building_geom = entities
            
    def _set_buildings_as_mesh_entities(self):
        
        self.simulation_model.\
            mesh_settings_new.\
            primary_topology.\
            topological_reference.\
            entities = self.building_geom
                
    def _update_spec(self, simulation_spec):
        self.simulation_api.update_simulation(self.project_id, self.simulation_id, simulation_spec)
        
    def set_mesh_fineness(self, fineness): 
        '''
        Set the mesh refinement
        
        
        Parameters
        ----------
        fineness : A string with either one of the following: 
           VERY_COARSE; COARSE ; MODERATE ; FINE ; VERY_FINE
        Returns
        -------
        None.

        '''
        self.simulation_model.mesh_settings_new.new_fineness.type = fineness
        
    def set_surface_roughness(self, surface_roughness, name = "ground"):
        '''
        Assign surface roughness 
        
        Parameters
        ----------
        surface_roghness : float 
        The equivalent sand grain surface roughness value
        Returns
        -------
        None.
        
        '''


        self.surface_roughness = sim.models.surface_roughness.SurfaceRoughness(
            name = name,
            surface_roughness = sim.DimensionalLength(value=float(surface_roughness),
                unit="m"),
            topological_reference = self.topological_reference)
        
        self.advanced_modelling.surface_roughness = self.surface_roughness


    def set_topological_reference(self, entities = [], sets = []): 
        
        '''
        Define the topological entity at which the surface roughness would be applied

        Parameters
        ----------
        entities: list of type string
        sets    : list of type string

        Reqiured entities and sets for the identification of the CAD part 

        '''
        
        entities = [self.building_geom.name]
        self.topological_reference =sim.models.topological_reference.TopologicalReference(entities, sets)

    def import_ladybug_grid(self, path, name):
        '''
        Imports a point grid from ladybug tools.
        
        The grid should be created in ladybug tools and cast to file 
        from a panel.

        Parameters
        ----------
        path : pathlib.Path
            Path to the file that holds the cast file.
            
        name : str
            A name for the grid to be saved as, this will be used as the 
            probe point name in SimScale.

        Returns
        -------
        None.

        '''
        sc.import_ladybug_grid(self, path, name)
        
    def import_csv_grid_with_numbers(self, path, name):
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
        df = pd.read_csv(path, header=0, names=["X", "Y", "Z"])
        
        df = df.rename('P{}'.format)
        self.grid[name] = {}
        self.grid[name]['data'] = df

    def upload_probe_plots(self, fraction_from_end=0.2):
        '''
        Uploads all defined probe points in the analysis type to SimScale

        Returns
        -------
        None.

        '''
        grids = self.grid
        project_id = self.project_id
        for key in grids:
            print("uploading probe plot: {}".format(key))
            path = pathlib.Path.cwd() / "{}.csv".format(key)
            grids[key]['data'].to_csv(path)

            probe_points_csv_storage = self.storage_api.create_storage()
            with open(path, 'rb') as file:
                self.api_client.rest_client.PUT(url=probe_points_csv_storage.url,
                                                headers={'Content-Type': 'application/octet-stream'},
                                                body=file.read())
            storage_id = probe_points_csv_storage.storage_id

            probe_points_table_import = sim.TableImportRequest(location=sim.TableImportRequestLocation(storage_id))
            probe_points_table_import_response = self.table_import_api.import_table(project_id,
                                                                                    probe_points_table_import)
            table_id = probe_points_table_import_response.table_id

            probe_plot = sim.ProbePointsResultControl(
                name=key,
                write_control=sim.ModerateResolution(),
                fraction_from_end=fraction_from_end,
                probe_locations=sim.TableDefinedProbeLocations(table_id=table_id)
            )

            grids[key]['id'] = table_id
            
            self.plot_ids.append(probe_plot)
            
        self.grid = grids
        
    def _set_probe_plots(self):
        self.simulation_model.result_control.probe_points = self.plot_ids
        
    def run_all_directions(self):
        '''
        Takes all predefined directions and runs them in parrallel

        Returns
        -------
        None.

        '''
        directions = self.get_wind_directions()
        for key in directions:
            
            self._set_abl_table(key)
            self._set_wind_tunnel(str(key))
            self._update_spec(self.simulation_spec)

            # Create simulation run
            name="Direction - {} - run {}".format(key, 1)
            self.runs[key] = name
            simulation_run = sim.SimulationRun(name=name)
            simulation_run = self.run_api.create_simulation_run(self.project_id, self.simulation_id, simulation_run)
            run_id = simulation_run.run_id

            simulation_run = self.run_api.get_simulation_run(self.project_id, self.simulation_id, run_id)

            self.run_api.start_simulation_run(self.project_id, self.simulation_id, run_id)

            self.run_api.update_simulation_run(self.project_id, self.simulation_id, run_id, simulation_run)

            self.run_ids[key] = run_id

    def get_wind_directions(self):
        '''
        Return all defined wind directions

        Returns
        -------
        key object
            A key object of all the defined wind profiles.

        '''
        return self.wind_profile_id.keys()

    def find_runs(self, run_number):
        '''
        Take a project Name, return a project
    
        Parameters
        ----------
        run_number : int
            The suffix of the names given, for example, direction 0.0, 
            run 1, the run number is 1.
    
        Returns
        -------
        run_ids : list
            A list of id's that share the run number.
    
        '''
        run_api = self.run_api

        run_string = "run {}".format(run_number)

        runs = run_api.get_simulation_runs(self.project_id, self.simulation_id).to_dict()['embedded']
        run_ids = {}
        for run in runs:
            if run_string in run['name']:
                key = run['name'].replace("Direction - ", "").replace(" - run {}".format(run_number), "")
                run_ids[key] = run["run_id"]

        return run_ids

    def set_run_ids(self, run_number):
        '''
        Sets run ID's post solve.
        
        This is useful if you have a solve, and just want to post process
        or download the results.
        
        Parameters
        ----------
        run_number : int
            The suffix of the names given, for example, direction 0.0, 
            run 1, the run number is 1..

        Returns
        -------
        None.

        '''
        self.run_ids = self.find_runs(run_number)
        
    def get_run_names(self):
        run_names = []
        for key in self.run_ids.keys():
            run = self.run_api.get_simulation_run(self.project_id, 
                                                  self.simulation_id, 
                                                  self.run_ids[key])
            
            run_names.append(run.name)
            
    def monitor_simulation(self, interval=100):
        import time
        
        
        simulation_status = {}
        for key in self.run_ids.keys():
            run = self.run_api.get_simulation_run(self.project_id, 
                                                  self.simulation_id, 
                                                  self.run_ids[key])
                    
            
            simulation_status[self.run_ids[key]] = {'run': run,
                                                    'status': run.status}
        
        def update_status(simulation_status):
            print_dict = {}
            for key in simulation_status.keys():
                
                simulation_status[key]['run'] = self.run_api.get_simulation_run(
                    self.project_id, 
                    self.simulation_id, 
                    key)
                
                simulation_status[key]['status'] = simulation_status[key]['run'].status
                print_dict[simulation_status[key]['run'].name] = simulation_status[key]['status']
            return simulation_status, print_dict
        
        def check_all_statuses(simulation_status):
            check_no=0
            for key in simulation_status.keys():
                if simulation_status[key]['status'] in ("FINISHED", "CANCELED", "FAILED"):
                    check_no += 1
                    
            if check_no == len(simulation_status):
                exit_code = 1
            else:
                exit_code = 0
            return exit_code
        
        while check_all_statuses(simulation_status) == 0:
            
            simulation_status, print_dict = update_status(simulation_status)
            print(print_dict)
            time.sleep(interval)
        

class model_obj:
    
    def __init__(self):
        self.model = sim.IncompressiblePacefish(
            bounding_box_uuid=[],
            flow_domain_boundaries=sim.FlowDomainBoundaries(
                xmin=sim.VelocityInletBC(
                    name="Velocity inlet (A)",
                    velocity=sim.FixedMagnitudeVBC(
                            type="FIXED_VALUE_NO_EXPRESSION",
                            value=sim.DimensionalFunctionSpeed(
                                value=sim.TableDefinedFunction(
                                    type="TABLE_DEFINED",
                                    label="upload",
                                    table_id=None,
                                    result_index=[
                                        2,
                                    ],
                                    independent_variables=[
                                        sim.TableFunctionParameter(
                                            reference=1,
                                            parameter="HEIGHT",
                                            unit="m",
                                        ),
                                    ],
                                    separator=",",
                                    out_of_bounds="CLAMP",
                                ),
                                unit="m/s",
                            ),
                        ),
                    turbulence_intensity=sim.TurbulenceKineticEnergyTIBC(
                            type="TURBULENCE_KINETIC_ENERGY",
                            value=sim.DimensionalFunctionTurbulenceKineticEnergy(
                                value=sim.TableDefinedFunction(
                                    type="TABLE_DEFINED",
                                    label="upload",
                                    table_id=None,
                                    result_index=[
                                        3,
                                    ],
                                    independent_variables=[
                                        sim.TableFunctionParameter(
                                            reference=1,
                                            parameter="HEIGHT",
                                            unit="m",
                                        ),
                                    ],
                                    separator=",",
                                    out_of_bounds="CLAMP",
                                ),
                                unit="m²/s²",
                            ),
                        ),
                    dissipation_type=sim.CustomOmegaDissipation(
                            type="CUSTOM_DISSIPATION",
                            value=sim.DimensionalFunctionSpecificTurbulenceDissipationRate(
                                value=sim.TableDefinedFunction(
                                    type="TABLE_DEFINED",
                                    label="upload",
                                    table_id=None,
                                    result_index=[
                                        4,
                                    ],
                                    independent_variables=[
                                        sim.TableFunctionParameter(
                                            reference=1,
                                            parameter="HEIGHT",
                                            unit="m",
                                        ),
                                    ],
                                    separator=",",
                                    out_of_bounds="CLAMP",
                                ),
                                unit="1/s",
                            ),
                        ),
                    ),
                xmax=sim.PressureOutletBC(name="Pressure outlet (B)"),
                ymin=sim.WallBC(name="Side (C)", velocity=sim.SlipVBC()),
                ymax=sim.WallBC(name="Side (D)", velocity=sim.SlipVBC()),
                zmin=sim.WallBC(
                    name="Ground (E)",
                    velocity=sim.NoSlipVBC(
                        no_slip_wall_roughness_type=sim.NoSlipWallEquivalentSandRoughness(
                            surface_roughness=sim.DimensionalLength(value=0, unit="m")
                        )
                    ),
                ),
                zmax=sim.WallBC(name="Top (F)", velocity=sim.SlipVBC()),
            ),
            simulation_control=sim.FluidSimulationControl(
                end_time=sim.DimensionalTime(value=5, unit="s"),
                max_run_time=sim.DimensionalTime(value=100000, unit="s"),
            ),
            advanced_modelling=sim.AdvancedModelling(),
            result_control=sim.FluidResultControls(
                forces_moments=[],
                probe_points=[],
                transient_result_control=sim.TransientResultControl(
                    write_control=sim.CoarseResolution(),
                    export_fluid=True,
                    geometry_primitive_uuids=[],
                ),
                statistical_averaging_result_control=sim.StatisticalAveragingResultControlV2(
                    sampling_interval=sim.CoarseResolution(),
                    export_fluid=True,
                    geometry_primitive_uuids=[]
                ),
                snapshot_result_control=sim.SnapshotResultControl(
                    export_fluid=True,
                    geometry_primitive_uuids=[],
                ),
            ),
            mesh_settings_new=sim.PacefishAutomesh(
                new_fineness=sim.PacefishFinenessCoarse(),
                reference_length_computation=sim.AutomaticReferenceLength(),
                primary_topology=sim.BuildingsOfInterest(
                    type='BUILDINGS_OF_INTEREST',
                    topological_reference = sim.TopologicalReference(
                        entities=[],
                        sets=[],
                    ),
                )
            ),
        )