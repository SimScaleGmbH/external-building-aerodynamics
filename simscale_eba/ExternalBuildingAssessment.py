import pathlib
import time

import simscale_sdk as sim

import simscale_eba.SimulationCore as sc


class PedestrianComfort():

    def __init__(self, credentials=None):
        self.project = None
        self.simulation = None
        self.runs = []
        self.geometry = None
        self.flow_domain = None
        self.simulation_spec = None

        self.building_geom = None
        self.geometry_path = None
        self.geometry_name = None

        self.project_id = None
        self.simulation_id = None
        self.run_ids = {}
        self.geometry_id = None
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
            sc.create_client(self)
            
        else:
            sc.get_keys_from_client(self)
        
        sc.create_api(self)

    def find_project(self, name):
        '''
        Take a project Name, return a project
    
        Parameters
        ----------
        name : string
            The exact name of the project, best copied from the SimScale 
            UI.
    
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
        sc.find_project(self, name)

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
            self.find_project(name)
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
            self.find_geometry(name)
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

    def find_geometry(self, name):
        '''
        Take a Simulation Name, return a simulation
    
        Parameters
        ----------
        name : string
            The exact name of the simulation, best copied from the SimScale 
            UI.
    
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

    def set_region_of_interest(self, roi):
        self.region_of_interest = roi
        self.create_vertical_slice()

    def create_simulation(self, name):
        try:
            self.find_simulation(name)
            print("Cannot create simulation with the same name, using existing simulation")
            self.update_setup()
        except:
            self.create_spec_lbm(name)
            self.create_setup()

    def find_simulation(self, name):
        '''
        Take a Simulation Name, return a simulation
    
        Parameters
        ----------
        name : string
            The exact name of the simulation, best copied from the SimScale 
            UI.
    
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

    def create_setup(self):
        self.create_wind_tunnel()
        self.simulation = self.simulation_api.create_simulation(self.project_id, self.simulation_spec)
        self.simulation_id = self.simulation.simulation_id

    def update_setup(self):
        self.create_wind_tunnel()
        self.update_spec_lbm(0)

    def create_wind_tunnel(self, direction=0):
        self.get_geometry_map()

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

            rotation_angles=sim.DimensionalVectorAngle(value=sim.DecimalVector(x=0, y=0, z=-90 - int(direction)),
                                                       unit='°'),
        )
        self.flow_domain = external_flow_domain
        if direction == 0:
            self.flow_domain_id = self.simulation_api.create_geometry_primitive(self.project_id,
                                                                                external_flow_domain).geometry_primitive_id

        self.direction_flow_domain_ids[direction] = self.simulation_api.create_geometry_primitive(self.project_id,
                                                                                                  external_flow_domain).geometry_primitive_id

    def update_spec_lbm(self, direction):

        #Migrate all of the updating steps into separate functions and do everything to self.simulation_spec

        '''
        Update the relevent lbm specs to change the direction.
        
        The updated parts are:
            -Runtime
            -ABL profile        
            -Surface roughness
            -Meshing

        Parameters
        ----------
        direction : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        abl = self.test_conditions._atmospheric_boundary_layers[str(direction)]
        reference_speed = abl._reference_speed

        domain_length = self.region_of_interest._wt_length
        number_of_fluid_passes = self.number_of_fluid_passes

        simulation_time_period = number_of_fluid_passes * (domain_length / reference_speed)

        simulation_spec = self.simulation_api.get_simulation(self.project_id, self.simulation_id)

        simulation_spec.model.bounding_box_uuid = self.direction_flow_domain_ids[direction]

        simulation_spec.model.simulation_control = sim.FluidSimulationControl(
            end_time=sim.DimensionalTime(
                value=int(simulation_time_period),
                unit="s",
            ),
            max_run_time=sim.DimensionalTime(
                value=100000,
                unit="s",
            ),
        )
        #update surface roughness (currently fails due to incomaptible JSON format 07/08/2022)
        # simulation_spec.model.advanced_modelling = self.advanced_modelling
        
        #update mesh settings 
        self.set_mesh_settings

        simulation_spec.model.flow_domain_boundaries = sim.FlowDomainBoundaries(
            xmin=sim.VelocityInletBC(
                name="Wind Inflow",
                type="VELOCITY_INLET_V3",
                velocity=sim.FixedMagnitudeVBC(
                    type="FIXED_VALUE_NO_EXPRESSION",
                    value=sim.DimensionalFunctionSpeed(
                        value=sim.TableDefinedFunction(
                            type="TABLE_DEFINED",
                            label="upload",
                            table_id=self.wind_profile_id[str(direction)],
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
                            table_id=self.wind_profile_id[str(direction)],
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
                            table_id=self.wind_profile_id[str(direction)],
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
            xmax=sim.PressureOutletBC(
                name="Wind Outflow",
                type="PRESSURE_OUTLET_V30",
            ),
            ymin=sim.WallBC(
                name="Wind Tunnel Side (1)",
                type="WALL_V34",
                velocity=sim.SlipVBC(
                    type="SLIP",
                ),
            ),
            ymax=sim.WallBC(
                name="Wind Tunnel Side (2)",
                type="WALL_V34",
                velocity=sim.SlipVBC(
                    type="SLIP",
                ),
            ),
            zmin=sim.WallBC(
                name="Wind Tunnel Floor",
                type="WALL_V34",
                velocity=sim.NoSlipVBC(
                    type="NO_SLIP",
                    surface_roughness=sim.DimensionalLength(
                        value=0,
                        unit="m",
                    ),
                ),
            ),
            zmax=sim.WallBC(
                name="Wind Tunnel Ceiling",
                type="WALL_V34",
                velocity=sim.SlipVBC(
                    type="SLIP",
                ),
            ),
        )

        # print(self.simulation_spec.model.mesh_settings_new)
        # print(simulation_spec)
        self.simulation_api.update_simulation(self.project_id, self.simulation_id, simulation_spec)
        self.simulation_spec = simulation_spec

    def create_spec_lbm(self, name):
        '''
        Create an LBM setup, that is not specific to the direction aligned to north

        Parameters
        ----------
        name : str
            The name to be given to the simulation.

        Returns
        -------
        None.

        '''
        self.upload_probe_plots()
        model = sim.IncompressiblePacefish(
            bounding_box_uuid=self.flow_domain_id,
            type="INCOMPRESSIBLE_PACEFISH",
            turbulence_model="KOMEGASST_DDES",
            material=sim.IncompressibleMaterial(
                type="INCOMPRESSIBLE",
                name="Material: Air",
                viscosity_model=sim.NewtonianViscosityModel(
                    type="NEWTONIAN",
                    kinematic_viscosity=sim.DimensionalKinematicViscosity(
                        value=1.529E-5,
                        unit="m²/s",
                    ),
                ),
                density=sim.DimensionalDensity(
                    value=1.1965,
                    unit="kg/m³",
                ),
                reference_temperature=sim.DimensionalTemperature(
                    value=293.15,
                    unit="K",
                ),
                molar_weight=sim.DimensionalMolarMass(
                    value=28.97,
                    unit="kg/kmol",
                ),
            ),
            flow_domain_boundaries=sim.FlowDomainBoundaries(
                xmin=sim.VelocityInletBC(
                    name="Wind Inflow",
                    type="VELOCITY_INLET_V3",
                    velocity=sim.FixedMagnitudeVBC(
                        type="FIXED_VALUE_NO_EXPRESSION",
                        value=sim.DimensionalFunctionSpeed(
                            value=sim.TableDefinedFunction(
                                type="TABLE_DEFINED",
                                label="upload",
                                table_id=self.wind_profile_id[list(
                                    self.wind_profile_id.keys())[0]],
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
                                table_id=self.wind_profile_id[list(
                                    self.wind_profile_id.keys())[0]],
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
                                table_id=self.wind_profile_id[list(
                                    self.wind_profile_id.keys())[0]],
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
                xmax=sim.PressureOutletBC(
                    name="Wind Outflow",
                    type="PRESSURE_OUTLET_V30",
                ),
                ymin=sim.WallBC(
                    name="Wind Tunnel Side (1)",
                    type="WALL_V34",
                    velocity=sim.SlipVBC(
                        type="SLIP",
                    ),
                ),
                ymax=sim.WallBC(
                    name="Wind Tunnel Side (2)",
                    type="WALL_V34",
                    velocity=sim.SlipVBC(
                        type="SLIP",
                    ),
                ),
                zmin=sim.WallBC(
                    name="Wind Tunnel Floor",
                    type="WALL_V34",
                    velocity=sim.NoSlipVBC(
                        type="NO_SLIP",
                        surface_roughness=sim.DimensionalLength(
                            value=0,
                            unit="m",
                        ),
                    ),
                ),
                zmax=sim.WallBC(
                    name="Wind Tunnel Ceiling",
                    type="WALL_V34",
                    velocity=sim.SlipVBC(
                        type="SLIP",
                    ),
                ),
            ),
            simulation_control=sim.FluidSimulationControl(
                end_time=sim.DimensionalTime(
                    value=10,
                    unit="s",
                ),
                max_run_time=sim.DimensionalTime(
                    value=10000,
                    unit="s",
                ),
            ),
            advanced_modelling=sim.AdvancedModelling(
                surface_roughness=[],
                porous_objects=[],
                rotating_walls=[],
            ),
            result_control=sim.FluidResultControls(
                forces_moments=[],
                probe_points=self.plot_ids,
                field_calculations=[],
                transient_result_control=sim.TransientResultControl(
                    type="TRANSIENT",
                    write_control=sim.ModerateResolution(
                        type="MODERATE_RESOLUTION",
                    ),
                    fraction_from_end=0.2,
                    export_fluid=True,
                    export_surface=False,
                    geometry_primitive_uuids=[self.vertical_slice],
                ),
                statistical_averaging_result_control=sim.StatisticalAveragingResultControlV2(
                    type="STATISTICAL_AVERAGING_V2",
                    fraction_from_end=0.2,
                    sampling_interval=sim.ModerateResolution(
                        type="MODERATE_RESOLUTION",
                    ),
                    export_fluid=True,
                    export_surface=False,
                    geometry_primitive_uuids=[self.vertical_slice],
                ),
                snapshot_result_control=sim.SnapshotResultControl(
                    type="SNAPSHOT",
                    export_fluid=True,
                    export_surface=False,
                    geometry_primitive_uuids=[self.vertical_slice],
                ),
            ),
            mesh_settings_new=sim.PacefishAutomesh(
                type="PACEFISH_AUTOMESH",
                new_fineness=sim.PacefishFinenessCoarse(
                    type="COARSE",
                ),
                reference_length_computation=sim.ManualReferenceLength(
                    type="MANUAL_REFERENCE_LENGTH",
                    value=sim.DimensionalLength(value=self.region_of_interest._radius * 2,
                                                unit="m"
                                                ),

                ),
                primary_topology=sim.BuildingsOfInterest(
                    type="BUILDINGS_OF_INTEREST",
                    topological_reference=sim.TopologicalReference(
                        entities=[self.building_geom.name],
                        sets=[],
                    ),
                ),
                refinements=[],
            ),
        )
        simulation_spec = sim.SimulationSpec(name=name, geometry_id=self.geometry_id, model=model)
        self.simulation_spec = simulation_spec
        self.model = model

    def upload_abl_profiles(self):
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
        self.mesh_fineness = fineness
        
    def set_mesh_settings(self): 
        '''
        Define the required settings for the mesh.
        
        Returns
        -------
        None.

        '''
        self.simulation_spec.model.mesh_settings_new=sim.PacefishAutomesh(
            type="PACEFISH_AUTOMESH",
            new_fineness=sim.PacefishFinenessCoarse(
                type=self.mesh_fineness,
            ),
            reference_length_computation=sim.ManualReferenceLength(
                type="MANUAL_REFERENCE_LENGTH",
                value=sim.DimensionalLength(value=self.region_of_interest._radius * 2,
                                            unit="m"
                                            ),
    
            ),
            primary_topology=sim.BuildingsOfInterest(
                type="BUILDINGS_OF_INTEREST",
                topological_reference=sim.TopologicalReference(
                    entities=[self.building_geom.name],
                    sets=[],
                ),
            ),
            refinements=[],
        ),
        
    def set_advanced_modelling(self, AdvancedModelling):
        '''
        Set advanced modelling concept to the analysis
        

        Parameters
        ----------
        AdvancedModelling : AdvancedModelling object 
            A class inside the Simscale SDK that allows to set advanced concepts 
            such as surface_roughness , Porous media, and Rotating zones 
        Returns
        -------
        None.

        '''
        self.advanced_modelling = AdvancedModelling
                
        
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


    def set_topological_reference(self,entities = [], sets = []): 
        
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

    def get_geometry_map(self):
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
        maps = self.geometry_api.get_geometry_mappings(project_id, geometry_id, _class='body',
                                                       bodies=[self.geometry_name])
        if len(maps.embedded) == 1:
            mesh_geom = maps.embedded[0]
            self.building_geom = mesh_geom
        else:
            pass

    def create_vertical_slice(self):
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

        self.vertical_slice = _slice.geometry_primitive_id

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

    def upload_probe_plots(self):
        '''
        Uploads all defined probe points in the analysis type to SimScale

        Returns
        -------
        None.

        '''
        grids = self.grid
        plot_ids = self.plot_ids
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
                probe_locations=sim.TableDefinedProbeLocations(table_id=table_id)
            )

            grids[key]['id'] = table_id
            plot_ids.append(probe_plot)
        self.grid = grids
        self.plot_ids = plot_ids

    def run_all_directions(self):
        '''
        Takes all predefined directions and runs them in parrallel

        Returns
        -------
        None.

        '''
        directions = self.get_wind_directions()
        for key in directions:
            self.create_wind_tunnel(direction=float(key))
            self.update_spec_lbm(float(key))

            # Create simulation run
            simulation_run = sim.SimulationRun(name="Direction - {} - run {}".format(key, 1))
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
