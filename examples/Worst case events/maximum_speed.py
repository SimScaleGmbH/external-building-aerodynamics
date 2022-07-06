import pathlib
import sys

import numpy as np

sys.path.append('E:\Current Cases\SimScale Objects\simscale')

import simscale_eba.HourlyContinuous as hc
import simscale_eba.BoundaryLayer as abl

historic = hc.HourlyContinuous()

# Put any path here
path = r'..\..\weather_files\climate-source-file_thermalComfort.xlsx'
historic.import_city_of_london_historic(pathlib.Path(path))

weather_stats = hc.WeatherStatistics()
weather_stats.set_directions(np.arange(0, 360, 10))
weather_stats.set_speeds(np.arange(0.5, 16, 1))
weather_stats.set_hourly_continuous(historic)

weather_stats.plot_probability_distributions()
weather_stats.get_highest_speeds(periods='quarter')
weather_stats.get_gumbel_extreeme_speed(in_years=100)
weather_stats.plot_gumbel_correlation()

print("Maximum speed in return period is {}".format(weather_stats.extreeme_speed))

bl = abl.AtmosphericBoundaryLayer()
bl.set_atmospheric_boundary_layer(aerodynamic_roughness=0.03,
                                  reference_speed=10,
                                  reference_height=10
                                  )

#correction_dict = bl.get_correction_factor(speed=weather_stats.extreeme_speed)
correction = bl.get_correction_factor(speed=36, height=20)
print("Correction factor from reference height and speed is {}".format(correction.speed_correction_factor))
print("Correction factor from reference height and pressure is {}".format(correction.pressure_correction_factor))
print(bl._reference_speed)
import matplotlib.pyplot as plt


fig, ax = plt.subplots()

line_1 = ax.plot(bl._u, bl._height, linewidth=2.0, color='dodgerblue')
line_2 = ax.plot(bl._u*correction.speed_correction_factor, bl._height, color='k', linewidth=2.0)

if correction.reference_height.m == correction.correction_height.m:
    ax.set_yticks([correction.reference_height.m], 
                  labels=[r"$H_{ref}$ = $H_{Correction Height}$" + " = {}".format(
                      str(correction.reference_height))])
    
    #Horizontal lines
    line_3 = ax.plot([0, np.max([correction.referrence_speed.m, correction.correction_speed.m])], 
                     [correction.reference_height.m, correction.reference_height.m],
                     color='k', linestyle='--')
    
    line_4 = ax.plot([correction.referrence_speed.m, correction.referrence_speed.m], 
                     [0, correction.reference_height.m],
                     color='dodgerblue', linestyle='--')
    
    line_5 = ax.plot([correction.correction_speed.m, correction.correction_speed.m], 
                     [0, correction.correction_height.m],
                     color='k', linestyle='--')
else:
    ax.set_yticks([correction.reference_height.m, correction.correction_height.m], labels=["$H_{ref}$", "$H_{Correction Height}$"])
    
    #Horizontal lines
    line_3 = ax.plot([0, correction.referrence_speed.m], 
                     [correction.reference_height.m, correction.reference_height.m],
                     color='dodgerblue', linestyle='--')
    
    line_4 = ax.plot([0, correction.correction_speed.m], 
                     [correction.correction_height.m, correction.correction_height.m],
                     color='k', linestyle='--')
    
    line_5 = ax.plot([correction.referrence_speed.m, correction.referrence_speed.m], 
                     [0, correction.reference_height.m],
                     color='dodgerblue', linestyle='--')
    
    line_6 = ax.plot([correction.correction_speed.m, correction.correction_speed.m], 
                     [0, correction.correction_height.m],
                     color='k', linestyle='--')
    
ax.set_xticks([correction.referrence_speed.m, correction.correction_speed.m], labels=["$U_{ref}$", "$U_{Correction Height}$"])

ax.set_xlabel('Streamwise Speed (m/s)')
ax.set_ylabel('Height (m)')
ax.set_ylim(0, 100)
ax.set_xlim(left=0)