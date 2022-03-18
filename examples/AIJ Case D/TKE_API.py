# -*- coding: utf-8 -*-
"""
Created on Mon Aug  2 19:34:28 2021

@author: MohamadKhairiDeiri
"""

import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import simscale_eba.ResultProcessing as res

result = res.directional_result()
result.find_project("AIJ Case D - LBM_ validation -updated")
result.find_simulation("Case D - 0 Deg - 02/12/2020")
result.find_run("Log Law - Custom Resolution")
result.query_results()
results = result.results
options = result.return_result_options()

category = "PROBE_POINT_PLOT_STATISTICAL_DATA"
name = "Validation Points"
item = result.download_result(category, name)

download_dict = result.download_dict

path = download_dict[category][name][None]

results = res.probes_to_dataframe(path)
k = results["k"]

# Calculate STDDEV_modeled from the TKE_modeled

TKE_modeled = k["AVG"]
STDDEV_modeled = np.sqrt(2 / 3 * TKE_modeled)

# Calculate STDDEV_total of the problem (STDDEV_modeled + STDDEV_resolved(obtained from stddev of umag))
umag = results["UMag"]

STDDEV_resolved = umag["STDDEV"]
STDDEV_total = np.sqrt(np.square(STDDEV_modeled) + np.square(STDDEV_resolved))

# Calculate TKE_total from STDDEV_total and normalize it by Uh^2
TKE_total = (3 / 2 * np.square(STDDEV_total))
TKE_total_normalized = TKE_total / np.square(6.65)

# print(TKE_total_normalized)

# import experimental results for comparison

experimental_path = pathlib.Path.cwd() / "Case_D_Experimental_Results_TKE.xlsx"
experimental_results = pd.read_excel(experimental_path)
# print(experimental_results)


# plots
distribution = [3, 1]

mpl.rcParams['figure.dpi'] = 1200
fig, axs = plt.subplots(1, 2, gridspec_kw={'width_ratios': distribution})

l = axs[0].plot(k.index, TKE_total_normalized,
                k.index, experimental_results["TKE(Exp_S) / UH^2"], 'ks',
                markerfacecolor='none', markeredgecolor='black', markersize=3, )

axs[0].legend((l), ("SimScale - TKE ", "Experiment S"), loc='upper left', frameon=False,
              prop={"weight": "bold", "size": "5"})
axs[0].set_xlim(0, k.shape[0])
xlim = axs[0].get_xlim()
ylim = axs[0].get_ylim()
axs[0].set_ylim(0, 0.1)
axs[0].set_yticks([0, 0.05, 0.1])
axs[0].set_aspect(aspect=(xlim[1] / ylim[1]) / distribution[0])
axs[0].set_ylabel("TKE (-)")
axs[0].set_xlabel("Point Number")
X1 = experimental_results["TKE(Exp_S) / UH^2"].to_numpy()

Y = TKE_total_normalized.to_numpy()

# Find empty data
nanX1 = np.isnan(X1)

nanY = np.isnan(Y)

# Remove empty data
x1 = X1[np.invert(nanX1)]
y1 = Y[np.invert(nanX1)]

# print(x1, "\n", y1)

# fit line for
m1, b1, r_value1, p_value1, std_err1 = stats.linregress(x1, y1)
r_value1 = int(r_value1 * 100) / 100
# m1, b1 = np.polyfit(x1, y1, 1)


# Standard Error and Confidence Interval
std_error = stats.sem(TKE_total_normalized, ddof=1)
PopulationMean = np.mean(x1)
sampleMean = np.mean(TKE_total_normalized)
print("The sample Mean is =", sampleMean)
# 95% confidence Interval
lowerLimit = PopulationMean - (1.96 * std_error)
upperLimit = PopulationMean + (1.96 * std_error)
print("The 95% confidence Interval limits are:", "\n",
      "Upper Limit =", upperLimit, "\n",
      "Lower Limit =", lowerLimit, "\n")

print("********\n", std_error)

# Correlation plot
l = axs[1].plot(experimental_results["TKE(Exp_S) / UH^2"], TKE_total_normalized, "sg",
                x1, m1 * x1 + b1, "-g", " ",
                markersize=3, markerfacecolor='none')

axs[1].legend((l), ("Experiment S", "r={}".format(r_value1), "S.E={:.4f}".format(std_error)), loc='upper left',
              frameon=False, prop={"weight": "bold", "size": "5"})

axs[1].set_xlim(0, 0.1)
axs[1].set_ylim(0, 0.1)
axs[1].axline([0, 0], [0.1, 0.1])
axs[1].axline([0, 0], [1, 1], color="black")
# axs[1].set_yticks([0, 0.05, 0.1])

axs[1].set_aspect(aspect="equal")

fig.subplots_adjust(top=1.4)
fig.suptitle("SimScale vs Experimental Results, for AIJ Case D")
