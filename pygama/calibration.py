import sys
import numpy as np
from .peak_fitting import *
from .utils import get_bin_centers
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs
from scipy.signal import argrelextrema, medfilt
from scipy.ndimage.filters import gaussian_filter1d
from scipy.stats import norm
import scipy.optimize as op

#return a histogram around the most prominent peak in a spectrum of a given percentage of width
def get_most_prominent_peaks(energySeries, num_peaks=10, bins=2000):
    '''
    find the most prominent peaks in a spectrum by looking for spikes in derivative of spectrum

    energySeries: array of measured energies
    num_peaks = number of most prominent peaks to find
    '''

    # bins = np.linspace( np.amin(energySeries), np.amax(energySeries), 2700 )
    # bins = "auto"

    # automatic bins
    hist, bin_edges = np.histogram(energySeries, bins=bins)
    bin_centers = get_bin_centers(bin_edges)

    #median filter along the spectrum, do this as a "baseline subtraction"
    hist_med = medfilt(hist, 101)
    hist = hist - hist_med
    # plt.plot(bin_centers, hist_med, color="r")
    # plt.plot(bin_centers, hist-hist_med, color="k")
    # plt.show()
    # exit()

    #find the n most prominent peaks
    peak_idxs = argrelextrema(hist, np.greater_equal, order=8)[0]
    del_idxs = []
    for i in range(1, len(peak_idxs)):
        if peak_idxs[i-1] == peak_idxs[i]-1:
            del_idxs.append(i)
    peak_idxs = np.delete(peak_idxs, del_idxs)

    peak_vals = hist[peak_idxs]
    sort_idxs = np.argsort(peak_vals)
    peak_idxs_max = peak_idxs[sort_idxs[-num_peaks:]]

    peak_energies = np.sort(bin_centers[peak_idxs_max])
    bin_width = bin_edges[1]-bin_edges[0]
    return peak_energies, bin_width

    #the four highest peaks
    cal_es = [860, 2614]
    peak_es = peak_energies[-2:]

    from scipy.stats import linregress
    m,b,r,_,_=linregress(peak_es, y=cal_es)

    plt.figure()
    # plt.subplot(121)
    plt.plot(m*bin_centers+b, hist, ls="steps")
    # plt.plot(bin_centers, hist, ls="steps")
    # plt.subplot(122)
    # plt.plot(bin_centers, peaks_diff, ls="steps")
    #
    peak_energies = m*peak_energies+b
    for peak_e in peak_energies:
        plt.axvline(peak_e, color="g", ls=":")
        print(peak_e)
    #
    # for peak_e in peak_es:
    #     # plt.axvline(bin_centers[peak_idx], color="r", ls=":")
    #     plt.axvline(peak_e, color="r", ls=":")


    plt.show()
    exit()


def compare_peaks(data_peaks, cal_peaks, data_err):
    from itertools import combinations

    # dp_norm = (data_peaks - data_peaks[0] )/(data_peaks[-1]- data_peaks[0])
    # cp_norm = (cal_peaks - cal_peaks[0] )/(cal_peaks[-1]- cal_peaks[0])
    #
    #
    # # dp_adj = dp_norm*scale+offset

    cal_sets = combinations(range(len(cal_peaks)), len(cal_peaks))
    data_sets = combinations(range(len(data_peaks)), len(cal_peaks))
    def get_ratio_sum(cal, data):
        from scipy.stats import linregress
        m,b,r,_,_=linregress(data, y=cal)
        return  r**2, m, b

    best_r2=0
    best_m = None
    best_b = None

    for cal_set in cal_sets:
        cal = cal_peaks[list(cal_set)]
        for data_set in data_sets:
            data = data_peaks[list(data_set)]

            r2,m,b = get_ratio_sum(cal, data)

            if r2> best_r2:
                best_r2=r2
                best_m = m
                best_b = b

    dp_norm = best_m*data_peaks + best_b
    return best_m, best_b


def calibrate_tl208(energy_series, peak_energies="th228", plotFigure=None):
    '''
    energy_series: array of energies we want to calibrate
    peak_energies: array of peaks to fit

    1.) we find the 2614 peak by looking for the tallest peak at >0.1 the max adc value
    2.) fit that peak to get a rough guess at a calibration to find other peaks with
    3.) fit each peak in peak_energies
    4.) do a linear fit to the peak centroids to find a calibration
    '''

    cal_peaks = np.array([238.632, 510.770, 583.191, 727.330, 860.564, 2614.553])#get_calibration_energies(peak_energies)

    #get 10 most prominent ~high e peaks
    max_adc = np.amax(energy_series)
    energy_hi = energy_series[ (energy_series > np.percentile(energy_series, 20)) & (energy_series < np.percentile(energy_series, 99.9))]

    # plt.hist(energy_hi, bins=2700, histtype="step")
    # plt.show()
    # exit()

    peak_energies, peak_e_err = get_most_prominent_peaks(energy_hi, num_peaks=9)

    rough_kev_per_adc, rough_kev_offset = compare_peaks(peak_energies, cal_peaks, peak_e_err)
    e_cal_rough = rough_kev_per_adc*energy_series+rough_kev_offset

    # return rough_kev_per_adc, rough_kev_offset

    # for peak in cal_peaks:
    #     plt.axvline(peak, c="r", ls=":")
    #
    # plt.hist(e_cal_rough[e_cal_rough>100], bins=2700)
    # plt.show()
    # exit()

    ###############################################
    #Do a real fit to every peak in peak_energies
    ###############################################
    max_adc = np.amax(energy_series)

    peak_num = len(cal_peaks)
    centers = np.zeros(peak_num)
    fit_result_map = {}
    bin_size = 0.2 #keV

    if plotFigure is not None:
        plot_map = {}

    for i,energy in enumerate(cal_peaks):
        window_width = 10 #keV
        window_width_in_adc = (window_width)/rough_kev_per_adc
        energy_in_adc = (energy-rough_kev_offset)/rough_kev_per_adc
        bin_size_adc = (bin_size)/rough_kev_per_adc

        peak_vals = energy_series[ (energy_series > energy_in_adc -window_width_in_adc) &
                                 (energy_series < energy_in_adc +window_width_in_adc) ]

        peak_hist, bins = np.histogram(peak_vals, bins = np.arange(energy_in_adc -window_width_in_adc,
                                                             energy_in_adc +window_width_in_adc + bin_size_adc,
                                                         bin_size_adc))
        bin_centers = get_bin_centers(bins)
        # plt.ion()
        # plt.figure()
        # plt.plot(bin_centers,peak_hist,  color="k", ls="steps")

        # inpu = input("q to quit...")
        # if inpu == "q": exit()

        try:
            guess_e, guess_sigma, guess_area = get_gaussian_guess(peak_hist, bin_centers)
        except IndexError:
            print("\n\nIt looks like there may not be a peak at {} keV".format(energy))
            print("Here is a plot of the area I'm searching for a peak...")
            plt.ion()
            plt.figure(figsize=(12,6))
            plt.subplot(121)
            plt.plot(bin_centers,peak_hist,  color="k", ls="steps")
            plt.subplot(122)
            plt.hist(e_cal_rough, bins=2700, histtype="step" )
            input("-->press any key to continue...")
            sys.exit()

        plt.plot(bin_centers, gauss(bin_centers, guess_e, guess_sigma, guess_area), color="b")

        # inpu = input("q to quit...")
        # if inpu == "q": exit()

        bounds = ([0.9*guess_e, 0.5*guess_sigma, 0, 0,0,0, 0],
                   [1.1*guess_e, 2*guess_sigma, 0.1, 0.75, window_width_in_adc, 10, 5*guess_area])
        params = fit_binned(radford_peak, peak_hist, bin_centers, [guess_e, guess_sigma, 1E-3, 0.7,5,0, guess_area], )#bounds=bounds)

        plt.plot(bin_centers, radford_peak(bin_centers, *params), color="r")

        # inpu = input("q to quit...")
        # if inpu == "q": exit()

        fit_result_map[energy] = params
        centers[i] = params[0]

        if plotFigure is not None:
          plot_map[energy] = (bin_centers, peak_hist)

    #Do a linear fit to find the calibration
    linear_cal = np.polyfit(centers, cal_peaks, deg=1)

    if plotFigure is not None:


        plt.figure(plotFigure.number)
        plt.clf()

        grid = gs.GridSpec(peak_num, 3)
        ax_line = plt.subplot(grid[:, 1])
        ax_spec = plt.subplot(grid[:, 2])

        for i,energy in enumerate(cal_peaks):
            ax_peak = plt.subplot(grid[i, 0])
            bin_centers, peak_hist = plot_map[energy]
            params = fit_result_map[energy]
            ax_peak.plot(bin_centers*rough_kev_per_adc+rough_kev_offset, peak_hist, ls="steps-mid", color="k")
            fit = radford_peak(bin_centers, *params)
            ax_peak.plot(bin_centers*rough_kev_per_adc+rough_kev_offset, fit, color="b")

        ax_peak.set_xlabel("Energy [keV]")

        ax_line.scatter(centers, cal_peaks, )

        x = np.arange(0,max_adc,1)
        ax_line.plot(x, linear_cal[0]*x+linear_cal[1])
        ax_line.set_xlabel("ADC")
        ax_line.set_ylabel("Energy [keV]")

        energies_cal = energy_series * linear_cal[0] + linear_cal[1]
        peak_hist, bins = np.histogram(energies_cal, bins = np.arange(0, 2700))
        ax_spec.semilogy(get_bin_centers(bins), peak_hist, ls="steps-mid")
        ax_spec.set_xlabel("Energy [keV]")

    return linear_cal

def get_calibration_energies(cal_type):
    if cal_type == "th228":
        return np.array([238, 277, 300, 452, 510.77, 583.191, 727, 763,785, 860.564, 1620, 2614.533], dtype="double")
    else:
        raise ValueError
