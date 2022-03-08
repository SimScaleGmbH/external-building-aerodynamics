import pathlib

import numpy as np
import pandas as pd

h = 7
xh = np.array([0.25, 0.5, 1, 2, 3, 4, 5])

x0 = 1
xs = xh * h

path = pathlib.Path.cwd()

for x in xs:
    Z = np.arange(0.1, 12.1, 0.1).T

    X = (np.ones(Z.shape) * x).T
    Y = np.zeros(Z.shape).T

    data = np.array([X, Y, Z]).T
    df = pd.DataFrame(data=data, columns=["x", "y", "z"])

    df = df.rename('P{}'.format)

    name = "xh={}.csv".format(x / h)
    local_path = path / name
    df.to_csv(local_path, header=False)
