import pathlib

import matplotlib as mpl
import matplotlib.image as image
import matplotlib.pyplot as plt
import pandas as pd

import simscale_eba.ResultProcessing as res

experimental_velocity_path = pathlib.Path.cwd() / "AIJ_Case_G_Normalised_Velocity.xlsx"
experimental_velocity = pd.read_excel(experimental_velocity_path, index_col=0)

experimental_tke_path = pathlib.Path.cwd() / "AIJ_Case_G_Normalised_TKE.xlsx"
experimental_tke = pd.read_excel(experimental_tke_path, index_col=0)

ref_speed = 5.586

result = res.directional_result()
result.find_project("AIJ Case: G - API")
result.find_simulation("Case G - URANS - Power Law")
result.find_run("Run 1")
result.query_results()
results = result.results
options = result.return_result_options()

category = "PROBE_POINT_PLOT_STATISTICAL_DATA"
average_velocity_mag = {}
tke_dict = {}
velocity_rans_dict = {}
tke_rans_dict = {}
for i in range(1, 8):
    name = "Pole{}".format(i)
    result.download_result(category, name)

    download_dict = result.download_dict
    items = result._find_item(category, name)

    path = download_dict[category][name][None]

    results = res.probes_to_dataframe(path)

    source_points = pd.read_csv(pathlib.Path(name + ".csv"), index_col=0, header=None)
    source_points.columns = ["X", "Y", "Z"]

    u_mag = results["UMag"]
    tke_rans = results["k"]["AVG"]

    variance_rans = ((2 / 3) * tke_rans) ** 0.5
    variance_resolved = u_mag["STDDEV"]

    variance_total = (variance_rans ** 2 + variance_resolved ** 2) ** 0.5
    variance_total.index = source_points["Z"].round(1)

    tke_total = (3 / 2) * variance_total ** 2

    u_mag.index = source_points["Z"].round(1)

    average_velocity_mag[name] = u_mag["AVG"]
    tke_dict[name] = tke_total

    velocity_rans_path = pathlib.Path.cwd() / "AIJ_TU2_Velocity" / (name + ".csv")

    try:
        velocity_rans_dict[name] = pd.read_csv(velocity_rans_path, index_col=1)
    except:
        print("{} does not have reported RANS data".format(name))

    tke_rans_path = pathlib.Path.cwd() / "AIJ_TU2_TKE" / (name + ".csv")

    try:
        tke_rans_dict[name] = pd.read_csv(tke_rans_path, index_col=1)
    except:
        print("{} does not have reported RANS data".format(name))

label_dict = {
    "Pole1": 0.25,
    "Pole2": 0.5,
    "Pole3": 1,
    "Pole4": 2,
    "Pole5": 3,
    "Pole6": 4,
    "Pole7": 5,

}

mpl.rcParams['figure.dpi'] = 2400
aspect_image = 1 / 12
aspect_plot = 1 / 8

multiplier = aspect_image / aspect_plot
distribution = [1, multiplier, multiplier, multiplier, multiplier, multiplier, multiplier, multiplier]

fig, axs = plt.subplots(1, 8, sharey=True, gridspec_kw={'width_ratios': distribution})

im = image.imread('setup.png')

axs[0].imshow(im, extent=(0, 1, 0, 12), zorder=-1)
axs[0].set_aspect(aspect=aspect_image)
axs[0].set_ylabel("Height (m)", fontsize=5)
axs[0].set_yticks([1.5, 3, 4.5, 6, 9, 12])
axs[0].tick_params(axis='y', labelsize=5)
axs[0].tick_params(axis='x', labelsize=5)

for i in range(1, 8):
    result_name = "Pole{}".format(i)
    plot_list = []
    if result_name in velocity_rans_dict.keys():
        plot_list.append(velocity_rans_dict[result_name]["velocity"])
        plot_list.append(velocity_rans_dict[result_name].index)

        l2, = axs[i].plot(*plot_list, '-ro', markerfacecolor='none', markeredgecolor='red', markersize=3, linewidth=0.5,
                          markeredgewidth=0.5)
        l3, = axs[i].plot(experimental_velocity.iloc[:, i - 1], experimental_velocity.index, 'ko',
                          markerfacecolor='none', markeredgecolor='black', markersize=3, )
        l1, = axs[i].plot(average_velocity_mag[result_name] / ref_speed, average_velocity_mag[result_name].index)
        l = [l1, l2, l3]
        legen_plot = i
    else:
        l2, = axs[i].plot(experimental_velocity.iloc[:, i - 1], experimental_velocity.index, 'ko',
                          markerfacecolor='none', markeredgecolor='black', markersize=3, )
        l1, = axs[i].plot(average_velocity_mag[result_name] / ref_speed, average_velocity_mag[result_name].index)

    axs[i].set_xlim(0, 1)
    axs[i].set_ylim(0, 12)
    axs[i].set_title("x/H=" + str(label_dict[result_name]), fontsize=5)
    axs[i].set_xlabel("U/Uh (-)", fontsize=5)
    axs[i].grid(color='black', linestyle='--', linewidth=0.5)
    axs[i].tick_params(axis='x', labelsize=5)
    axs[i].set_aspect(aspect=aspect_plot)

# fig.subplots_adjust(bottom=-0.5)
handles, labels = axs[legen_plot].get_legend_handles_labels()

model = "uRANS"
labels = ["SimScale - {} - Power Law Profile".format(model), "AIJ - RANS", "Experimental"]
fig.legend(l,
           labels,
           loc='lower center',
           bbox_to_anchor=(0.5, 0.25),
           fontsize=5,
           frameon=False
           )

fig.suptitle("SimScale vs Experimental Results, for AIJ Case G", y=0.7)
plt.savefig('velocity_results.png')
# TKE Plot
aspect_image = 0.1 / 12
aspect_plot = 0.1 / 8

multiplier = aspect_image / aspect_plot
distribution = [1, multiplier, multiplier, multiplier, multiplier, multiplier, multiplier, multiplier]
fig, axs = plt.subplots(1, 8, sharey=True, gridspec_kw={'width_ratios': distribution})
axs[0].imshow(im, extent=(0, 0.1, 0, 12), zorder=-1)
axs[0].set_aspect(aspect=aspect_image)
axs[0].set_ylabel("Height (m)", fontsize=5)
axs[0].set_yticks([1.5, 3, 4.5, 6, 9, 12])
axs[0].set_xticks([0.05, 0.1])
axs[0].tick_params(axis='y', labelsize=5)
axs[0].tick_params(axis='x', labelsize=5)

for i in range(1, 8):
    result_name = "Pole{}".format(i)
    plot_list = []
    if result_name in tke_rans_dict.keys():
        plot_list.append(tke_rans_dict[result_name]["tke"])
        plot_list.append(tke_rans_dict[result_name].index)

        l2, = axs[i].plot(*plot_list, '-ro', markerfacecolor='none', markeredgecolor='red', markersize=3, linewidth=0.5,
                          markeredgewidth=0.5)
        l3, = axs[i].plot(experimental_tke.iloc[:, i - 1], experimental_tke.index, 'ko', markerfacecolor='none',
                          markeredgecolor='black', markersize=3, )
        l1, = axs[i].plot(tke_dict[result_name] / ref_speed ** 2, tke_dict[result_name].index)
        l = [l1, l2, l3]
        legen_plot = i
    else:
        l2, = axs[i].plot(experimental_tke.iloc[:, i - 1], experimental_tke.index, 'ko', markerfacecolor='none',
                          markeredgecolor='black', markersize=3, )
        l1, = axs[i].plot(tke_dict[result_name] / ref_speed ** 2, tke_dict[result_name].index)
    axs[i].set_xlim(0, 0.1)
    axs[i].set_ylim(0, 12)
    axs[i].set_xticks([0.05, 0.1])
    axs[i].set_title("x/H=" + str(label_dict[result_name]), fontsize=5)
    axs[i].set_xlabel("TKE/Uh² (-)", fontsize=5)
    axs[i].grid(color='black', linestyle='--', linewidth=0.5)
    axs[i].tick_params(axis='x', labelsize=5)
    axs[i].set_aspect(aspect=aspect_plot)

# fig.subplots_adjust(bottom=-0.5)
handles, labels = axs[1].get_legend_handles_labels()
labels = ["SimScale - {} - Power Law Profile".format(model), "AIJ - RANS", "Experimental"]
fig.legend(l,
           labels,
           loc='lower center',
           bbox_to_anchor=(0.5, 0.25),
           fontsize=5,
           frameon=False
           )

fig.suptitle("SimScale vs Experimental Results, for AIJ Case G", y=0.7)
plt.savefig('tke_results.png')
