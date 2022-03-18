# -*- coding: utf-8 -*-
"""
Created on Tue Aug  3 11:31:43 2021

@author: MohamadKhairiDeiri
"""

import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

import simscale_eba.ResultProcessing as res

result = res.directional_result()
result.find_project("AIJ Case D - LBM_ validation - Darren2")
result.find_simulation(" Case D - 0 Deg 02/12/2020 (Full Scale)")
result.find_run("ABLProbe|LogLaw|Moderate")
result.query_results()
results = result.results
options = result.return_result_options()

category = "PROBE_POINT_PLOT_STATISTICAL_DATA"
name = "ABL profile "
item = result.download_result(category, name)

download_dict = result.download_dict

path = download_dict[category][name][None]

# Get the results of the velocity and TKE
results = res.probes_to_dataframe(path)
# print(results)
# print("*******//*********")
Umag = results["UMag"]
TKE = results["k"]

ABL_initial_profile_path = pathlib.Path.cwd() / "Log_law_profile.csv"
experimental_path = pathlib.Path.cwd() / "ExpS_Initial_Profile.xlsx"

ABL_initial_profile = pd.read_csv(ABL_initial_profile_path)
experimental_results = pd.read_excel(experimental_path)

# print(experimental_results)
# print("*******//*********")
# print(ABL_initial_profile)

height = ABL_initial_profile["Height"]

Umag["height"] = height
TKE["height"] = height
print(Umag, "\n", TKE)

# Plots

distribution = [2, 2]
mpl.rcParams['figure.dpi'] = 1200

fig, axs = plt.subplots(1, 2, sharey=True)

# plot Experiment and velocity (probe location)
l = axs[0].plot(
    ABL_initial_profile["u"], ABL_initial_profile["Height"], 'k',
    Umag["AVG"], Umag["height"],
    experimental_results["U"], experimental_results["z"],
    'ks', markerfacecolor='none', markeredgecolor='black', markersize=3)

axs[0].legend((l), ("SimScale - Target ABL", "SimScale - Log Law ABL", "Experiment"),
              loc='upper left', frameon=False, prop={"weight": "bold", "size": "5"})

xlim = axs[0].get_xlim()
ylim = axs[0].get_ylim()

axs[0].set_ylabel("Height (m)")
axs[0].set_xlabel("Average Velocity (m/s)")

l = axs[1].plot(
    ABL_initial_profile["tke"], ABL_initial_profile["Height"], 'k',
    TKE["AVG"], Umag["height"],
    experimental_results["k"], experimental_results["z"], 'ks',
    markerfacecolor='none', markeredgecolor='black', markersize=3)

axs[1].legend((l), ("SimScale - Target TKE", "SimScale - TKE profile", "Experiment"), loc='upper left', frameon=False,
              prop={"weight": "bold", "size": "5"})
xlim = axs[1].get_xlim()
ylim = axs[1].get_ylim()

axs[1].set_xlabel("TKE (m2/s2)")
