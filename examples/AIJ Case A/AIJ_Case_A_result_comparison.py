# import pandas as pd
import matplotlib as mpl
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pathlib
import simscale_eba.ResultProcessing as res
from matplotlib.lines import Line2D
from scipy import stats

angle = 0  # hard coded for this angle
b = 10  # building width in meters

result = res.directional_result()
result.find_project("AIJ Case A")
result.find_simulation("New Omega Profile")
result.find_run("vFine - Full Region")
result.query_results()
results = result.results
options = result.return_result_options()

category = "PROBE_POINT_PLOT_STATISTICAL_DATA"
name = "Vertical"
result.download_result(category, name)

download_dict = result.download_dict
items = result._find_item(category, name)

path = download_dict[category][name][None]

results = res.probes_to_dataframe(path)
sim_U = results["Ux"]['AVG']
sim_V = results["Uy"]['AVG']
sim_W = results["Uz"]['AVG']

sim_speeds = pd.concat([sim_U, sim_V, sim_W], axis=1)

experimental_path = pathlib.Path.cwd() / "vertical_results.xlsx"
experimental_results = pd.read_excel(experimental_path)

exp_speeds = experimental_results[['U(m/s)', 'V(m/s)', 'W(m/s)']]
sim_speeds.columns = exp_speeds.columns

locations = experimental_results[['x/b', 'y/b', 'z/b']]
exp_plot_speeds = exp_speeds.to_numpy()
sim_plot_speeds = sim_speeds.to_numpy()

for i in range(exp_speeds.shape[0]):
    exp_plot_speeds[i, :] = ((exp_speeds.to_numpy()[i, :] / (5 * (5 / 3)))
                             + locations['x/b'].to_numpy()[i])
    sim_plot_speeds[i, :] = ((sim_speeds.to_numpy()[i, :] / (5 * (5 / 3)))
                             + locations['x/b'].to_numpy()[i])

exp_plot_speeds = pd.concat([locations,
                             pd.DataFrame(exp_plot_speeds,
                                          columns=exp_speeds.columns)],
                            axis=1)

sim_plot_speeds = pd.concat([locations,
                             pd.DataFrame(sim_plot_speeds,
                                          columns=exp_speeds.columns)],
                            axis=1)

exp_plot_speeds_grouped = dict(list(exp_plot_speeds.groupby('x/b')))
sim_plot_speeds_grouped = dict(list(sim_plot_speeds.groupby('x/b')))

fig, ax = plt.subplots(1, 2, sharey=False, dpi=1200)

for key in exp_plot_speeds_grouped.keys():
    ax[0].plot(exp_plot_speeds_grouped[key]["U(m/s)"], exp_plot_speeds_grouped[key]['z/b'], '-r', )
    ax[0].plot(sim_plot_speeds_grouped[key]["U(m/s)"], sim_plot_speeds_grouped[key]['z/b'], '-b', )

ax[0].set_xlabel('x/b')
ax[0].set_ylabel('z/b')
rect = patches.Rectangle((-0.5, 0), 1, 2, linewidth=1, edgecolor='k', facecolor='none')
ax[0].add_patch(rect)

legend_elements = [Line2D([0], [0], color='r', ls='-', lw=1, label='Experimental'),
                   Line2D([0], [0], color='b', ls='-', lw=1, label='SimScale')
                   ]

fig.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.1), ncol=1, frameon=False)
fig.suptitle('AIJ Case A: Component U(m/s)')

m1, b1, r_value1, p_value1, std_err1 = stats.linregress(exp_speeds['U(m/s)'], sim_speeds['U(m/s)'])
r_value1 = int(r_value1 * 1000) / 1000
ax[1].text(0.2, 0.9, 'r = {}'.format(r_value1), horizontalalignment='center', verticalalignment='center',
           transform=ax[1].transAxes)
ax[1].plot(exp_speeds['U(m/s)'], sim_speeds['U(m/s)'], 'o')
