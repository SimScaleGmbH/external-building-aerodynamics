import json
import pathlib


class simulation_status():

    def __init__(self):
        self.file_name = "simulation.status"
        self.result_directory = None

        self.project_name = None
        self.simulation_name = None
        self.run_name = None

        self.is_downloaded = None
        self.minimum_resolution = None

        self.download_paths = None
        self.field_paths = None
        self.points_path = None
        self.output_stl_paths = None

    def set_simulation(self, project, simulation, run):
        self.project_name = project
        self.simulation_name = simulation
        self.run_name = run

    def set_result_directory(self, path):
        self.result_directory = pathlib.Path(path)

        if ((self.result_directory.stem == "simulation")
                and (self.result_directory.suffix == ".status")):
            raise Exception("Path provided was to the simulation.status file,"
                            " Should however be the directory it is stored in")

    def check_simulation_status(self):
        if self.result_directory == None:
            raise Exception("No path was provided, cannot read status")

        json_path = self.result_directory / self.file_name
        
        signal = None
        try:

            with open(json_path, "r") as read_file:
                read_dict = json.load(read_file)
            match_project = self.project_name == read_dict["project_name"]
            match_simulation = self.simulation_name == read_dict["simulation_name"]
            match_run = self.run_name == read_dict["run_name"]
            match_resolution = self.minimum_resolution == read_dict["minimum_resolution"]
            is_downloaded = read_dict["is_result_downloaded"]

            if (match_project and match_simulation and match_run
                    and is_downloaded and match_resolution):

                print("Matched to already downloaded results")
                signal = True
            else:
                print("Results downloaded dont match")
                signal = False
        except:
            print("No results exist locally, downloading now...")
            signal = False

        return signal

    def read_simulation_status(self, path=None):

        if (self.result_directory == None) and (path == None):
            raise Exception("No path was provided, cannot read status")
        elif self.result_directory == None and path != None:
            self.result_directory = pathlib.Path(path)
        elif self.result_directory != None and path == None:
            pass
        else:
            print("A path was already set, using latest, but this might"
                  "lead to unexpected results")
            self.result_directory = path

        json_path = self.result_directory / self.file_name

        with open(json_path, "r") as read_file:
            read_dict = json.load(read_file)

        self.project_name = read_dict["project_name"]
        self.simulation_name = read_dict["simulation_name"]
        self.run_name = read_dict["run_name"]

        self.is_downloaded = read_dict["is_result_downloaded"]
        self.minimum_resolution = read_dict["minimum_resolution"]

        self.download_paths = read_dict["download_paths"]
        self.field_paths = read_dict["field_paths"]
        self.points_path = read_dict["points_path"]
        self.output_stl_paths = read_dict["output_stl_paths"]

    def write_simulation_status(self, boolean=None):
        '''
        Take the PWC project, simulation and run, place them in a json file
        
        Here we are telling the result directory that the results stored
        belong to a certain run, and later, we can read it, and if the 
        run being requested is the same, we need not download again.

        '''
        if boolean != None:
            self.is_downloaded = boolean
        elif boolean == None and self.is_downloaded != None:
            pass
        else:
            raise Exception("Is downloaded should be True or False")

        json_dictionary = {
            "project_name": self.project_name,
            "simulation_name": self.simulation_name,
            "run_name": self.run_name,
            "is_result_downloaded": self.is_downloaded,
            "minimum_resolution": self.minimum_resolution,
            "download_paths": self.download_paths,
            "field_paths": self.field_paths,
            "points_path": self.points_path,
            "output_stl_paths": self.output_stl_paths
        }

        json_object = json.dumps(json_dictionary, indent=4)

        json_path = self.result_directory / "simulation.status"

        with open(json_path, "w") as outfile:
            outfile.write(json_object)

    def update_download_path(self, direction, path):
        if self.download_paths is None:
            self.download_paths = {}

        self.download_paths[str(direction)] = path

    def update_field_path(self, field, path, is_dimensional=False):
        if self.field_paths is None:
            self.field_paths = {}

        dimensionality = None
        if is_dimensional:
            dimensionality = "dimensional_"
        else:
            dimensionality = "dimensionless_"

        self.field_paths[dimensionality + str(field)] = path
