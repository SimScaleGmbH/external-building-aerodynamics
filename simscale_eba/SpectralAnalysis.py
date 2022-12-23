import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class frequency_analysis:
    def __init__(self):
        self.data = None

        self.integral_length_scale = None
        self.ef100 = None
        self.sampling_frequency = None
        self.frequencies = None
        self.energy = None

    def set_data(self, data):
        self.data = data

    def compute_integral_length_scale(self):
        # Legacy code
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
        hatx = (ef * U_mean) / (4 * U_stddev**2)

        self.integral_length_scale = hatx
        self.ef100 = ef
        self.sampling_frequency = fs
        self.frequencies = aFreq
        self.energy = energy
        self.length = L


def test_integral_lenght_scale(show_plot=False):
    # Here we test the integral length scale computation
    # Expected results:
    expected_ILS = 0.006431769932128274
    expected_ef100 = 0.008682610136218636

    # Read csv result file from SimScale
    component = "UMag_AIJ_Case_C"
    probe = "65"
    path = pathlib.Path.cwd() / "{}.csv".format(component)
    data = pd.read_csv(path, index_col="Time (s)")

    data = data["{}".format(probe)]

    # Perfrom frequency analysis
    freq_analysis = frequency_analysis()
    freq_analysis.set_data(data)
    freq_analysis.compute_integral_length_scale()

    # Print results
    error_ILS = (expected_ILS - freq_analysis.integral_length_scale) / (expected_ILS)
    error_ef100 = (expected_ef100 - freq_analysis.ef100) / (expected_ef100)

    print("Test Integral Length Scale computation:")
    print()
    print("Expected values:")
    print(f"Ingegral Length Scale: {expected_ILS}")
    print(f"E(f)100: {expected_ef100}")
    print()
    print("Computed Values:")
    print(f"Ingegral Length Scale: {freq_analysis.integral_length_scale}")
    print(f"E(f)100: {freq_analysis.ef100}")
    print()
    print("Computed Errros:")
    print(f"Ingegral Length Scale: {error_ILS:%}")
    print(f"E(f)100: {error_ef100:%}")

    if not show_plot:
        return

    # Plot the energy spectrum
    plt.plot(
        freq_analysis.frequencies,
        freq_analysis.energy[2 : int((freq_analysis.length / 2 + 1))],
    )
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Frequency, (hz)")
    plt.ylabel("E(f), (m2/s")
    plt.title(f"Frequency Analysis of Velocity Component {component} Signal")
    plt.show()


if __name__ == "__main__":

    test_integral_lenght_scale(show_plot=True)
