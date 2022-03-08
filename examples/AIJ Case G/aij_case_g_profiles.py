# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 16:24:32 2021

@author: DarrenLynch
"""

import pathlib

import matplotlib.pyplot as plt

import simscale_eba.BoundaryLayer as abl

alpha = 0.22

power_law = abl.AtmosphericBoundaryLayer(
    reference_height=9,
    reference_speed=5.6
)

power_law.alpha = alpha
power_law.set_streamwise_speed("POWER")
power_law.set_tke(method="UNIFORM", value=3.02)
power_law.set_omega("YGCJ")

variables = ["u", "tke", "omega"]
path = pathlib.Path.cwd() / "Power_law_profile.csv"
power_law.to_csv(path, variables)

log_law = abl.AtmosphericBoundaryLayer(
    reference_height=9,
    reference_speed=5.6
)

log_law.alpha = alpha
log_law.get_z0_from_alpha()
log_law.set_u_star()
log_law.set_streamwise_speed("LOGLAW")
log_law.set_tke("YGCJ")
log_law.set_omega("YGCJ")

fig, axs = plt.subplots(1, 3, sharey=True)

l1, l11 = axs[0].plot(power_law._u,
                      power_law._height,
                      "b",
                      log_law._u,
                      log_law._height,
                      "r")

axs[0].set_xlabel('Velocity (m/s)')
axs[0].set_ylabel('Height (m)')
axs[0].set_ylim(0, 12)

l2 = axs[1].plot(power_law._tke,
                 power_law._height,
                 "b",
                 log_law._tke,
                 log_law._height,
                 "r", )

axs[1].set_xlabel('TKE (m2/s2)')
# axs[2].set_ylabel('Height (m)')

l3 = axs[2].plot(
    power_law._omega,
    power_law._height,
    "b",
    log_law._omega,
    log_law._height,
    "r")

axs[2].set_xlabel('Omega (1/s)')
# axs[2].set_ylabel('Height (m)')
axs[2].set_xlim(0, 10)

fig.legend([l1, l11], ["Power Law", "Log Law"], loc="lower center")
fig.suptitle("Comparison between AIJ Case G ABL and the Log Law")
plt.subplots_adjust(bottom=0.3)
plt.show()

variables = ["u", "tke", "omega"]
path = pathlib.Path("E:\Current Cases\AIJ Case G") / "Log_law_profile.csv"
log_law.to_csv(path, variables)
