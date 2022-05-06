import os
import pathlib

import yaml

import simscale_sdk as sim

class SimscaleCredentials():

    def __init__(self,
                 api_key: str = '',
                 api_url: str = '',
                 version: str = '/v0',
                 header: str = 'X-API-KEY'):
        '''
        An object that takes care of the API Key, URL and Headers

        Parameters
        ----------
        version : str, optional
            The SimScale API version to use. 
            
            The default is '/v0'.
        header : str, optional
            The SimScale header version to use. 
            
            The default is 'X-API-KEY', it rarely needs changing.

        Returns
        -------
        None.

        '''
        self.api_key = api_key
        self.api_url = api_url
        
        self.configuration =None

        self.api_header = 'X-API-KEY'
        self.version = version
        self.host = ''

    def _get_variables_from_env(self):
        '''
        looks in your environment and reads the API variables
        
        SimScale API key and URL are read if they are set in the 
        environment as:
            
            SIMSCALE_API_KEY
            SIMSCALE_API_URL

        Returns
        -------
        None.

        '''
        try:
            self.api_key = os.getenv('SIMSCALE_API_KEY')
            self.api_url = os.getenv('SIMSCALE_API_URL')
            self._get_api_host()
        except:
            raise Exception("Cannot get Keys from Environment Variables")

    def _get_variables_from_yaml(self):
        '''
        looks in your API file and reads the API variables
        
        SimScale API key and URL are from the file: 
            %HOME%/.simscale_api_keys.yaml
            
        The yaml format should be:
            
            prod_api_keys:
                SIMSCALE_API_URL: "https://api.simscale.com"
                SIMSCALE_API_KEY: "insert your key"

        Returns
        -------
        None.

        '''
        path = pathlib.Path.home() / ".simscale_api_keys.yaml"

        with open(path, "r") as stream:
            try:
                yaml_dict = yaml.safe_load(stream)
                self.api_key = yaml_dict['prod_api_keys']['SIMSCALE_API_KEY']
                self.api_url = yaml_dict['prod_api_keys']['SIMSCALE_API_URL']

                self._get_api_host()

            except yaml.YAMLError as exc:
                raise Exception(exc)

    def _get_api_host(self):
        '''
        Create the host from API URL and Version

        Returns
        -------
        None.

        '''
        self.host = self.api_url + self.version
        
    def _is_variables_set(self):
        '''
        Check if the user explicitly provided variables as a string

        Returns
        -------
        None.

        '''
        print(self.api_key, self.api_url)
        if (not self.api_key) and (not self.api_url):
            print(False)
            return False
            
        else:
            print(True)
            return True
            
    
    def _is_env_variables_exist(self):
        '''
        Check to see if Environment Variables have been set
        
        This can be used to check if the setup is correct.

        Returns
        -------
        bool
            Returns True if set, false otherwise.

        '''
        try:
            self._get_variables_from_env()
            return True
        except:
            return False

    def _is_file_variables_exist(self):
        '''
        Check to see if API Key and URL have been saved in the file
        
        The file used is %HOME%/.simscale_api_keys.yaml
        
        This can be used to check if the setup is correct.

        Returns
        -------
        bool
            Returns True if saved, false otherwise.

        '''
        try:
            self._get_variables_from_yaml()
            return True
        except:
            return False
        
    def _create_configuration(self):
        configuration = sim.Configuration()
        configuration.host = self.api_host
        configuration.api_key = {
            self.api_key_header: self.api_key,
        }
        
        self.configuration = configuration

    def check_variables(self):
        '''
        Check API Key and URL from both the file and Environment
        
        Sets the API Key and URL from either the file or environment,
        but if both are set, use the file (to counter this simply delete
        the file).

        Raises
        ------
        Exception
            If API Key or URL is not set in either, raise an error.

        Returns
        -------
        None.

        '''
        is_var_set = self._is_variables_set()
        
        if not is_var_set:
            is_var_inenv = self._is_env_variables_exist()
            is_var_infile = self._is_file_variables_exist()
            if is_var_infile and not is_var_inenv:
                print(
                    "SimScale API Key and URL found in the file {}.".format(
                        pathlib.Path.home() / ".simscale_api_keys.yaml"))
            elif is_var_inenv and not is_var_infile:
                print(
                    "SimScale API Key and URL found in the environment variables")
            elif is_var_inenv and is_var_infile:
                print(
                    "SimScale API Key and URL found in the file {}".format(
                        pathlib.Path.home() / ".simscale_api_keys.yaml"),
                    " and in the environment variables, presidence is given to the prior.")
            else:
                raise Exception("Could not locate the ariables SIMSCALE_API_KEY",
                                " or SIMSCALE_API_URL on either file or in the"
                                " environment")
                
        self._create_configuration()

    def set_api_key(self, api_key: str):
        '''
        Manually set an API key as a string

        Parameters
        ----------
        api_key : str
            The API key associated with you account.
        '''
        self.api_key = api_key

    def set_api_url(self, api_url: str = "https://api.simscale.com"):
        '''
        Manually set an API URL as a string

        Parameters
        ----------
        api_url : str, optional
            The URL to use as the API URL, the default is the normal URL,
            however, there is a scenario this is different if working in
            a development server. The default is "https://api.simscale.com".

        Returns
        -------
        None.

        '''
        self.api_url = api_url

    def get_api_key(self):
        '''
        Get the API Key as a string

        Returns
        -------
        str
            A string that is the API Key.

        '''
        return self.api_key

    def get_api_url(self):
        '''
        Get the API URL as a string

        Returns
        -------
        str
            A string that is the URL.

        '''
        return self.api_url

    def get_api_header(self):
        '''
        Get the API header as a string

        Returns
        -------
        str
            A string that is the header.

        '''
        return self.api_header

    def get_api_host(self):
        '''
        Get the API host as a string

        Returns
        -------
        str
            A string that is the host.

        '''
        return self.host
    
    def get_config(self):
        '''
        Get the configuration of the client

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
        return self.configuration
    
    def create_yaml():
        '''
        todo
        
        Take API key and url, creates a yaml file in home.

        Returns
        -------
        None.

        '''
        pass
