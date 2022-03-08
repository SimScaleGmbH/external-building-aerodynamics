import pathlib

import numpy as np
import pandas as pd

import simscale_eba.ResultProcessing as pp

result = pp.directional_result()
result.find_project("Greenlite UK")
result.find_simulation("Facade Pressure Coefficients")
result.find_run("Run 2")
result.query_results()
options = result.return_result_options()

name = "Face4Floor2"
category = "PROBE_POINT_PLOT_STATISTICAL_DATA"
# result.download_result(category=category, name=name)

download_dict = result.download_dict
items = result._find_item(category, name)

direction = float(270)

for item in items:
    if item.direction == direction:
        result_set = item

url = result_set.download.url
data_responce = result.api_client.rest_client.GET(
    url=url,
    headers={result.api_key_header: result.api_key},
    _preload_content=False
)

probe_point_plot_statistical_data_csv = data_responce.data.decode('utf-8')

path = pathlib.Path.cwd()
output_path = path / "{}_{}_{}.csv".format(category, name, result.name)

with open(output_path, 'w', newline="") as file:
    file.write(probe_point_plot_statistical_data_csv)
file.close()

df = pd.read_csv(output_path)
avg_pressure = dict(list(df.groupby("VARIABLE")))["p"]
avg_pressure.index = avg_pressure["ITEM NAME"]
avg_pressure = avg_pressure["AVG"]
avg_cp = avg_pressure / (0.5 * 1.2 * 10 ** 2)

scenario_pressure = avg_cp * (0.5 * 1.2 * 4.62 ** 2)


class window():

    def __init__(self,
                 name,
                 _type="TOP_HUNG",
                 width=1,
                 height=1,
                 angle=10,
                 density=1.2):

        self.name = name
        self.width = width
        self.height = height
        self.opening_angle = float(angle)
        self.type = _type
        self.rho = density

        self.flow_rate = np.array([0, 0.25, 0.5, 1, 2, 4]).reshape((-1, 1))
        self.dp = None

        self.stroke_length = None
        self.length_ratio = None
        self.gradient = None
        self.max_cd = None
        self.cd0 = 0.62  # Orifice Dichcarge Coefficient
        self.a_eq = None  # equivilent_area
        self.a_eff = None  # effective area
        self.a_free = None  # free area

        self.cd = None
        self.dp = None

        self.df = None

    def set_top_hinged(self):
        self.length_ratio = self.width / self.height
        self.stroke_length = np.sin((self.opening_angle * np.pi) / (2 * 180))
        self.a_free = self.width * self.height

        _dict = {
            "1": {"lower bound": 0, "upper bound": 0.5, "gradient": 0.06, "cdmax": 0.612},
            "2": {"lower bound": 0.5, "upper bound": 1, "gradient": 0.048, "cdmax": 0.589},
            "3": {"lower bound": 1, "upper bound": 2, "gradient": 0.04, "cdmax": 0.563},
            "4": {"lower bound": 2, "upper bound": np.inf, "gradient": 0.038, "cdmax": 0.548},
        }

        for key in _dict.keys():
            if (self.length_ratio >= _dict[key]["lower bound"]
                    and self.length_ratio < _dict[key]["upper bound"]):
                self.gradient = _dict[key]["gradient"]
                self.max_cd = _dict[key]["cdmax"]

        self.cd = self.max_cd * (1 - np.exp(-self.gradient * self.opening_angle))

    def get_pressure_drop(self):
        self.dp = (self.rho / 2) * (self.flow_rate / (self.cd * self.a_free))
        return self.dp

    def to_dataframe(self):
        arr = np.concatenate((self.flow_rate, self.dp), axis=1)
        columns = ["V_dot (m3/s)", "dp (Pa)"]
        df = pd.DataFrame(arr, columns=columns)

        self.df = df

    def to_csv(self, path=pathlib.Path.cwd()):
        self.to_dataframe()
        path = path / (self.name + "{}".format(self.opening_angle) + '.csv')
        self.df.to_csv(path)


win = window("top_hung_1", width=0.9, height=1.6)
win.set_top_hinged()
dp = win.get_pressure_drop()

win.to_csv()
