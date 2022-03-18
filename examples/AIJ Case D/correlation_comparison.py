import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

name = "TemoporalIndipendence.csv"
path = pathlib.Path.cwd() / name
df = pd.read_csv(path, index_col=0)

X = np.arange(3)

mpl.rcParams['figure.dpi'] = 2400
fig1, ax = plt.subplots(figsize=(1, 1), dpi=1200)

# ax = fig1.add_axes([0,0,1,1])
test = df.iloc[1].to_numpy()

velocity = ax.bar(X + 0.00, df.iloc[0].to_numpy(), color='b', width=0.25)
tke = ax.bar(X + 0.25, df.iloc[1].to_numpy(), color='r', width=0.25)

ax.set_ylabel("R Value (-)", fontsize=5)
ax.set_xlabel("Temporal Resolution", fontsize=5)
ax.legend(labels=['Velocity', 'TKE'], loc='lower center', fontsize=3, bbox_to_anchor=(0.5, -0.6), frameon=False)
ax.set_ylim(0.5, 1)
ax.bar_label(velocity, padding=3, fontsize=3, rotation=90)
ax.bar_label(tke, padding=3, fontsize=3, rotation=90)

plt.title("Correlations of Different" + "\n" +
          "Temporal Resolutions", fontsize=7)
plt.xticks([0, 1, 2], ('Moderate', 'High', 'Very High'), fontsize=3)
plt.yticks(fontsize=3)

plt.savefig("temporal_resolutions.png", bbox_inches='tight')
