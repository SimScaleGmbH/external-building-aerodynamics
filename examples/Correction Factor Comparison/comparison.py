import simscale_eba.BoundaryLayer as bl

roughnesses = [0.003, 0.01, 0.05, 0.3, 1]

old_correctors = []
for roughness in roughnesses:
    abl = bl.AtmosphericBoundaryLayer()
    abl.set_atmospheric_boundary_layer(aerodynamic_roughness=roughness,
                                       reference_speed=10,
                                       method_dict={"u": "EUROCODE",
                                                    "tke": "YGCJ",
                                                    "omega": "YGCJ"
                                                    })
    old_correctors.append(float(abl.meteo_corrector))

print("The correctors based upon the Eurocode ABL Profiles are: \n{}".format(old_correctors))

new_correctors = []
for roughness in roughnesses:
    abl = bl.AtmosphericBoundaryLayer()
    abl.set_atmospheric_boundary_layer(aerodynamic_roughness=roughness,
                                       reference_speed=10,
                                       method_dict={"u": "LOGLAW",
                                                    "tke": "YGCJ",
                                                    "omega": "YGCJ"
                                                    })
    new_correctors.append(float(abl.meteo_corrector))

print("The correctors based upon the Loglaw ABL Profiles are: \n{}".format(new_correctors))
