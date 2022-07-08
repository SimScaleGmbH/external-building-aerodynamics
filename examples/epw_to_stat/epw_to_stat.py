import pathlib

import numpy as np

import simscale_eba.HourlyContinuous as hc

epw = hc.HourlyContinuous()

# Put any path here
path = r'USA_MA_Boston-Logan.Intl.AP.725090_TMYx.2004-2018.epw'
epw.import_epw(pathlib.Path(path))

weather_stats = hc.WeatherStatistics()
weather_stats.set_directions(np.arange(0, 360, 10))
weather_stats.set_speeds(np.arange(0.5, 16, 1))
weather_stats.set_hourly_continuous(epw)

weather_stats.to_stat()
weather_stats.plot_cumulative_distributions()


#Plot Windrose
import matplotlib.pyplot as plt
from matplotlib import cm

table = weather_stats.standard_table.T
cum_table = np.cumsum(table.to_numpy(), axis=0)

fig, ax = plt.subplots(subplot_kw={"projection": "polar"})

labels = []
for i in range(0, len(weather_stats.speeds)):
    if i == 0:
        labels.append('U < {} m/s'.format(weather_stats.speeds[i]))
    else:
        labels.append('{} m/s >= U > {} m/s'.format(
            weather_stats.speeds[i-1], weather_stats.speeds[i]))

offset = np.pi / 2
width = (2 * np.pi / table.shape[1])
# Specify offset
ax.set_theta_offset(offset)
ax.set_theta_direction(-1)

# Set limits for radial (y) axis. The negative lower bound creates the whole in the middle.
#ax.set_ylim(0)

# Remove all spines
ax.set_frame_on(False)

# Remove grid and tick marks
ax.xaxis.grid(False)
ax.yaxis.grid(False)

print(type(table.columns.to_numpy()))
angles = np.radians(table.columns)

colors = cm.winter(weather_stats.speeds / 10)

bars = []
for i in range(0, table.shape[0]):
    if i == 0:
        bar = ax.bar(angles, table.iloc[i, :],
                      width=width, linewidth=1,
                      color=colors[i, :], edgecolor="black"
                      )
    else:
        bar = ax.bar(angles, table.iloc[i, :],
                     width=width, linewidth=1,
                     color=colors[i, :], edgecolor="black",
                     bottom=cum_table[i-1, :]
                     )
    bars.append(bar)

ax.legend(bars, labels, loc=5, bbox_to_anchor=(2, 0.5), frameon=False)