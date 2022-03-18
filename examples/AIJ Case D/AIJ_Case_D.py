import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import simscale_eba.BoundaryLayer as abl

experimental_path = pathlib.Path.cwd() / "Case_D_Experimental.xlsx"
experimental = pd.read_excel(experimental_path.as_posix())

reference_speed = 6.61
roughness = 0.043  # at full scale
log_law = abl.AtmosphericBoundaryLayer(
    reference_height=100,
    reference_speed=reference_speed,
    aerodynamic_roughness=roughness  # at full scale
)

log_law.set_u_star()
log_law.set_streamwise_speed("LOGLAW")
log_law.set_u_star()
log_law.set_tke("YGCJ", c1=0.4, c2=0.6)
# log_law.set_tke("YGCJ")
log_law.set_omega("YGCJ")

power_law = abl.AtmosphericBoundaryLayer(
    reference_height=100,
    reference_speed=reference_speed,
    aerodynamic_roughness=roughness
)

power_law.get_alpha_from_z0()
power_law.set_streamwise_speed("POWER")
power_law.set_u_star()
power_law.set_tke(method="YGCJ")
power_law.set_omega("YGCJ")

experimental_abl = abl.AtmosphericBoundaryLayer()
u = np.concatenate(([0], experimental["u (m/s)"].to_numpy()))
experimental_abl._height = np.concatenate(([0], experimental["z (m)"].to_numpy()))
experimental_abl._u = u
experimental_abl._tke = np.concatenate(([0], experimental["tke (m2/s)"].to_numpy()))
experimental_abl.set_omega("AIJ")


def nan_helper(y):
    """Helper to handle indices and logical indices of NaNs.

    Input:
        - y, 1d numpy array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    """

    return np.isnan(y), lambda z: z.nonzero()[0]


y = experimental_abl._omega
nans, x = nan_helper(y)
y[nans] = np.interp(x(nans), x(~nans), y[~nans])

experimental_abl._omega = y

fig, axs = plt.subplots(1, 3, sharey=True)

l = axs[0].plot(
    experimental_abl._u / reference_speed,
    experimental_abl._height,
    power_law._u / reference_speed,
    power_law._height,
    log_law._u / reference_speed,
    log_law._height,
    "r")

# l.get_lines()

axs[0].set_xlabel('Velocity (-)')
axs[0].set_ylabel('Height (m)')
axs[0].set_ylim([0, 100])

l2 = axs[1].plot(
    experimental_abl._tke,
    experimental_abl._height,
    power_law._tke,
    power_law._height,
    log_law._tke,
    log_law._height,
    "r")

axs[1].set_xlabel('TKE (m2/s2)')
# axs[2].set_ylabel('Height (m)')

l3 = axs[2].plot(
    experimental_abl._omega,
    experimental_abl._height,
    power_law._omega,
    power_law._height,
    log_law._omega,
    log_law._height,
    "r")

axs[2].set_xlabel('Omega (1/s)')
axs[2].set_xlim([0, 20])
# axs[2].set_ylabel('Height (m)')

fig.legend(l, ["Experimental",
               "Power Law",
               "Log Law"],
           loc="lower center")

fig.suptitle("Comparison between AIJ Case D ABL, the Log Law and Power Law")
plt.subplots_adjust(bottom=0.3)

plt.show()

variables = ["u", "tke", "omega"]
path = pathlib.Path.cwd() / "Log_law_profile.csv"
log_law.to_csv(path, variables)

variables = ["u", "tke", "omega"]
path = pathlib.Path.cwd() / "Experimental_profile.csv"
experimental_abl.to_csv(path, variables)
