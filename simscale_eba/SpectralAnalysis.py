import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.signal


class frequency_analysis:
    def __init__(self):
        self.time = None
        self.signal = None
        self.sampling_frequency = None

        self.integral_length_scale = None
        self.ef100 = None
        
        self.frequencies = None
        self.energy = None

        self.PSD = None
        self.spectrum = None

    def set_data(self, t, x):
        """
        Set time history data to be analyzed

        Parameters
        ==========
        t: time array
        x: signal array
        """
        self.time = t
        self.signal = x
        self.sampling_frequency = 1 / (t[1] - t[0])

    def compute_integral_length_scale(self):
        # Legacy code, just modified to fit updated workflow
        # The aim is to leverage here the other spectrum
        # computation methods in the future
        signal = self.signal
        U_mean = np.mean(signal)
        U_stddev = np.std(signal)

        aFData = np.real(np.fft.rfft(signal))
        L = len(aFData)
        n = int(L / 2)

        power = np.power(np.abs(aFData), (2 / L))
        # aFMag = np.abs(aFData[1:n]/L)

        # time = self.time
        fs = self.sampling_frequency
        aFreq = fs * (np.arange(1, n) / n)
        energy = power / fs
        ef = np.mean(energy[2:100])
        hatx = (ef * U_mean) / (4 * U_stddev**2)

        self.integral_length_scale = hatx
        self.ef100 = ef
        self.frequencies = aFreq
        self.energy = energy
        self.length = L

    def __compute_spectrum(self, scaling="spectrum", method="periodogram"):
        """
        Compute the multiple spectrums of the signal:

        - Spectrum [V**2]
        - Power Spectral Density [V**2 / Hz]

        With different methods:

        - Welch
        - Periodogram

        The parameters for the methods were selected after testing
        for short signals, obtained from the LBM simulations.

        Parameters
        ----------
        scaling: "spectrum", "density"
        method: "welch", "periodogram"

        Returns
        -------
        f: frequency range of the spectrum
        S2: Power
        """
        if method == "welch":
            f, S2 = scipy.signal.welch(
                self.signal,
                self.sampling_frequency,
                detrend="constant",
                window="hamming",
                nperseg=512,
                noverlap=256,
                scaling=scaling,
            )

        elif method == "periodogram":
            f, S2 = scipy.signal.periodogram(
                self.signal,
                self.sampling_frequency,
                detrend="linear",
                window="hamming",
                scaling=scaling,
            )

        return f, S2

    def compute_psd(self):
        """
        Compute the Power Spectral Density of the signal.

        Note that if the input signal has units of [V],
        the output spectrum has units [V**2 / Hz].
        """
        f, S2 = self.__compute_spectrum(scaling="density")

        self.frequencies = f
        self.PSD = S2

    def compute_spectrum(self):
        """
        Compute the Power Spectral Density of the signal.

        Note that if the input signal has units of [V],
        the output spectrum has units [V**2].
        """
        f, S2 = self.__compute_spectrum(scaling="spectrum")

        self.frequencies = f
        self.spectrum = S2


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

    t = data.index
    x = data[f"{probe}"].to_numpy()

    # Perfrom frequency analysis
    freq_analysis = frequency_analysis()
    freq_analysis.set_data(t, x)
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

def test_compute_spectrums(show_plot=False):
    """
    Test spectrum computation for accuracy.
    """
    rng = np.random.default_rng()

    # Generate a 2 Vrms sine wave signal at 1234 Hz
    # corrupted by 0.001 V**2/Hz noise
    fs = 10e3  # Hz - sampling rate
    N = 1e5  # Number of samples

    Arms = 2.0  # V - Sine RMS
    A = Arms * np.sqrt(2)  # V - Sine amplitude
    f0 = 1234.0  # Hz - Sine frequency

    noise_power = 0.001  # V**2/Hz - power density
    noise_amplitude = np.sqrt(noise_power * fs / 2)  # V

    t = np.arange(N) / fs
    x = A * np.sin(2 * np.pi * f0 * t)
    # Add random gaussian noise
    x += rng.normal(scale=noise_amplitude, size=t.shape)

    # Compute Power Spectral Density
    freq_analysis = frequency_analysis()
    freq_analysis.set_data(t, x)
    freq_analysis.compute_psd()

    print(f"Sampling frecuency (expected): {fs}")
    print(f"Sampling frecuency (computed): {freq_analysis.sampling_frequency}")

    fPX = freq_analysis.frequencies
    PX = freq_analysis.PSD

    # Noise power of the signal
    # Use second half to avoid peak
    # Take the mean to filter error
    computed_noise_power = np.mean(PX[int(N/4):])
    error_noise_power = (noise_power - computed_noise_power) / noise_power
    print(f"Noise power density:")
    print(f"Computed: {computed_noise_power:.3e} (V**2/Hz)")
    print(f"Expected: {noise_power:.3e}  (V**2/Hz)")
    print(f"Error: {error_noise_power:%}")

    # Spectrum
    # Remember this computes squared spectrum!
    freq_analysis.compute_spectrum()

    fSX = freq_analysis.frequencies
    SX = np.sqrt(freq_analysis.spectrum)

    # The peak gives the estimate of the RMS amplitude
    computed_Arms = SX.max()
    error_Arms = (Arms - computed_Arms) / Arms
    print()
    print(f"RMS amplitude:")
    print(f"Computed: {computed_Arms:.3e} (V)")
    print(f"Expected: {Arms:.3e} (V)")
    print(f"Error: {error_Arms:%}")

    if not show_plot:
        return

    # Plots
    plt.figure()

    plt.plot(t, x)

    plt.xlabel("Time (s)")
    plt.ylabel("x(t) (V)")
    plt.title("Time History")

    plt.figure()

    plt.plot(fPX, PX)

    plt.yscale("log")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Sx(f) (V**2/Hz)")
    plt.title("Power Spectral Density ")

    plt.figure()

    plt.plot(fSX, SX)

    plt.yscale("log")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Sx(f)  (V RMS)")
    plt.title("Spectrum")

    plt.show()    


if __name__ == "__main__":

    # test_integral_lenght_scale(show_plot=True)
    test_compute_spectrums(show_plot=True)
