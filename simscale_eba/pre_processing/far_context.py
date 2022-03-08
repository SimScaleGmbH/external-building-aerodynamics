import matplotlib.pyplot as plt
import numpy as np


class ring():

    def __init__(self, radius, building_size, centre=[0, 0, 0]):
        self.centre = centre
        self.radius = radius
        self.building_size = building_size
        self.ring_index = None

        self.building_spacing_factor = 1

        self.buildings = []

    def generate_buildings(self):
        circumference = 2 * np.pi * self.radius

        no_of_buildings = int(circumference
                              / self.building_size
                              * (1 + self.building_spacing_factor))

        theta = 360 / no_of_buildings

        X = []
        Y = []

        for i in np.arange(0.0, 360.0, theta):
            X.append(self.radius * np.cos(i))
            Y.append(self.radius * np.sin(i))

        return X, Y


ring = ring(350, 20)
X, Y = ring.generate_buildings()

plt.scatter(X, Y)
