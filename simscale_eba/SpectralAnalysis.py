import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

component = "UMag_AIJ_Case_C"
probe = "65"
path = pathlib.Path.cwd() / "{}.csv".format(component)
data = pd.read_csv(path, index_col="Time (s)")

data = data["{}".format(probe)]


class frequency_analysis():

    def __init__(self):
        self.data = None

        self.integral_length_scale = None
        self.ef100 = None
        self.sampling_frequency = None
        self.frequencies = None
        self.energy = None

    def set_data(self, data):
        self.data = data

    def get_integral_length_scale(self):
        data = self.data
        signal = data.to_numpy()
        U_mean = np.mean(signal)
        U_stddev = np.std(signal)

        aFData = np.real(np.fft.rfft(signal))
        L = len(aFData)
        n = int(L / 2)

        power = np.power(np.abs(aFData), (2 / L))
        # aFMag = np.abs(aFData[1:n]/L)

        # time = data[probe]
        fs = 1 / (data.index[1] - data.index[0])
        aFreq = fs * (np.arange(1, n) / n)
        energy = power / fs
        ef = np.mean(energy[2:100])
        hatx = (ef * U_mean) / (4 * U_stddev ** 2)

        self.integral_length_scale = hatx
        self.ef100 = ef
        self.sampling_frequency = fs
        self.frequencies = aFreq
        self.energy = energy
        self.length = L


freq_analysis = frequency_analysis()
freq_analysis.set_data(data)
freq_analysis.get_integral_length_scale()

plt.plot(freq_analysis.frequencies, freq_analysis.energy[2:int((freq_analysis.length / 2 + 1))])
plt.xscale('log')
plt.yscale('log')
plt.xlabel("Frequency, (hz)")
plt.ylabel("E(f), (m2/s")
plt.title("Frequency Analysis of Velocity Component {} Signal".format(component))
