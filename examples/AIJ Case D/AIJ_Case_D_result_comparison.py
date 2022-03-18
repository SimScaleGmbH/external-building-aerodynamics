# import pandas as pd
import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import simscale_eba.ResultProcessing as res

angle = 0  # hard coded for this angle

result = res.directional_result()
result.find_project("AIJ Case D - LBM_ validation -updated")
result.find_simulation("Case D - 0 Deg - 02/12/2020")
result.find_run("Log Law - Custom Resolution")
result.query_results()
results = result.results
options = result.return_result_options()

category = "PROBE_POINT_PLOT_STATISTICAL_DATA"
name = "Validation Points"
result.download_result(category, name)

download_dict = result.download_dict
items = result._find_item(category, name)

path = download_dict[category][name][None]

results = res.probes_to_dataframe(path)
u_mag = results["UMag"]

experimental_path = pathlib.Path.cwd() / "Case_D_Experimental_Results.xlsx"
experimental_results = pd.read_excel(experimental_path)

# Plots
mpl.rcParams['figure.dpi'] = 2400
distribution = [3, 1]
fig1 = plt.figure(1, figsize=(15, 3), dpi=1200)

plt.plot(u_mag.index, u_mag["AVG"] / 6.61,
         u_mag.index, experimental_results["U/U_ref - S"], 'ks',
         u_mag.index, experimental_results["U/U_ref - T"], 'ko', markerfacecolor='none', markeredgecolor='black',
         markersize=3, )

axes = plt.gca()

# set aspect ratio
ratio = 0.2

plt.legend(("SimScale - Log Law ABL", "Experiment T", "Experiment S"), loc='upper left', frameon=False,
           prop={"weight": "bold", "size": "8"})
axes.set_xlim(0, u_mag.shape[0])
xleft, xright = axes.get_xlim()
ybottom, ytop = axes.get_ylim()
axes.set_aspect(abs((xright - xleft) / (ybottom - ytop)) * ratio)
axes.set_ylim(0, 1)
axes.set_yticks([0, 0.5, 1])
# axes.set_aspect(aspect=(xlim[1]/ylim[1])/distribution[0])
axes.set_ylabel("Wind Speed (-)", fontsize=15)
axes.set_xlabel("Point Number", fontsize=15)
plt.title("SimScale vs Experimental Results, for AIJ Case D", fontsize=15)
plt.savefig("WindSpeed_{}.png".format(str(angle)), bbox_inches='tight')
plt.show()

X1 = experimental_results["U/U_ref - S"].to_numpy()
X2 = experimental_results["U/U_ref - T"].to_numpy()

Y = u_mag["AVG"].to_numpy() / 6.61

# Find empty data
nanX1 = np.isnan(X1)
nanX2 = np.isnan(X2)

nanY = np.isnan(Y)

# Remove empty data
x1 = X1[np.invert(nanX1)]
y1 = Y[np.invert(nanX1)]

# fit line for
m1, b1, r_value1, p_value1, std_err1 = stats.linregress(x1, y1)
r_value1 = int(r_value1 * 100) / 100
# m1, b1 = np.polyfit(x1, y1, 1)

x2 = X2[np.invert(nanX2)]
y2 = Y[np.invert(nanX2)]

m2, b2 = np.polyfit(x2, y2, 1)
m2, b2, r_value2, p_value2, std_err2 = stats.linregress(x2, y2)
r_value2 = int(r_value2 * 1000) / 1000

fig2 = plt.figure(2, figsize=(4, 4), dpi=600)

plt.plot(experimental_results["U/U_ref - S"], u_mag["AVG"] / 6.61, "sg",
         experimental_results["U/U_ref - T"], u_mag["AVG"] / 6.61, "or",
         x1, m1 * x1 + b1, "-g",
         x2, m2 * x2 + b2,
         "-r", markersize=2, markerfacecolor='none')

axes = plt.gca()

plt.legend(("Experiment T", "Experiment S", "r={}".format(r_value1), "r={}".format(r_value2)), loc='upper left',
           frameon=False, prop={"weight": "bold", "size": "7"})
axes.set_xlim(0, 1)
axes.set_ylim(0, 1)
axes.set_ylabel("Experimental Wind Speed (-)", fontsize=15)
axes.set_xlabel("SimScale Wind Speed", fontsize=15)
axes.axline([0, 0], [1, 1], color="black")
axes.set_aspect(aspect="equal")
plt.title("Correlation: SimScale vs Experiment", fontsize=15)
plt.savefig("correlation_{}.png".format(str(angle)), bbox_inches='tight')
plt.show()
