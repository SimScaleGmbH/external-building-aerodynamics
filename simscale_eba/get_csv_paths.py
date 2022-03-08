import pathlib

import numpy as np
import pandas as pd

csv_paths = list(pathlib.Path(r'D:\Pacefish Turbulent Inlet').glob('**/*.csv'))

csv_stems = []
csv_index = []
for path in csv_paths:
    stem = path.stem
    csv_stems.append(stem)
    csv_index.append(int(str(stem).strip("fluctuations_point_")))

array = np.array([csv_stems, csv_paths]).T
path_dataframe = pd.DataFrame(array, index=csv_index, columns=["name", "path"])

path_5 = path_dataframe.loc[5]
