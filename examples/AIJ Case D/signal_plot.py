import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

import simscale_eba.ResultProcessing as res


def get_signal(run_name, probe_number):
    result = res.directional_result()
    result.find_project("AIJ Case D - LBM_ validation -updated")
    result.find_simulation("Case D - 0 Deg - 02/12/2020")
    result.find_run(run_name)
    result.query_results()
    # results = result.results
    # options = result.return_result_options()
    # print(options)

    category = "PROBE_POINT_PLOT"
    name = "Validation Points"
    quantity = "UMag"
    result.download_result(category, name, quantity)
    items = result.download_dict

    df = pd.read_csv(items[category][name][quantity], index_col="Time (s)")
    return df[str(probe_number)]


runs = ["Log Law - Custom Resolution", "Log Law - High Resolution", "LogLawUpdated|VeryFine"]

# Plots
mpl.rcParams['figure.dpi'] = 2400
distribution = [3, 1]
fig1 = plt.figure(1, figsize=(15, 3), dpi=1200)

signals = []
for run in runs:
    signal = get_signal(run, 5)
    signals.append(signal)
    plt.plot(signal.index, signal)

plt.legend(("Very High", "High", "Moderate"), loc='upper left', frameon=False, prop={"weight": "bold", "size": "8"})
plt.ylabel("Wind Speed (m/s)", fontsize=15)
plt.xlabel("Time (s)", fontsize=15)
plt.savefig("signal.png", bbox_inches='tight')
plt.show()
