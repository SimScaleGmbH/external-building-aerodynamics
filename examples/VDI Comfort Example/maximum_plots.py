import numpy as np
import pandas as pd

vdi_frequency_bins = [0.01, 0.05, 0.2, 1, 5, 10]

no_frequencies = len(vdi_frequency_bins)
test_import = pd.read_csv('comfort_map_VDI {}.csv'.format(vdi_frequency_bins[0]), index_col=0)
no_points = test_import.shape[0]
Compiled_df = pd.DataFrame(np.zeros(shape=(no_points, no_frequencies)))

i = 0
for frequency in vdi_frequency_bins:
    columns = ['x', 'y', 'z', 'comfort']
    df = pd.read_csv('comfort_map_VDI {}.csv'.format(frequency), index_col=0)
    df.columns = columns

    Compiled_df.iloc[:, i] = df.loc[:, 'comfort']

    i += 1

worst_category = Compiled_df.max(axis=1)
xyz = test_import.iloc[:, 0:3]

result = pd.concat([xyz, worst_category], axis=1)
columns = ['x', 'y', 'z', 'comfort']
result.columns = columns
result.to_csv('comfort_map_VDI.csv')
