import numpy as np
from .peak_fitting import *
from .utils import get_bin_centers

#return a histogram around the most prominent peak in a spectrum of a given percentage of width
def get_most_prominent_peak(energySeries, peakEnergy, hist_width=20):
    '''
    energySeries: array of measured energies
    peakEnergy: energy of the peak youre trying to fit
    hist_width: side-bands on both sides of peak, in keV (roughly)
    '''

    #find the tl208 FEP peak (assuming its most prominent peak...)
    e_vals = energySeries

    # ~kev bins?
    hist, bin_edges = np.histogram(e_vals, bins=np.linspace( np.amin(e_vals), np.amax(e_vals), 2700 ))
    bin_centers = get_bin_centers(bin_edges)
    # plt.histogram(e_vals, bins="auto")

    tl08_energy = bin_centers[np.argmax(hist)] #rough energy, in adc
    rough_adc_per_kev = (tl08_energy /peakEnergy ) #rough guess at adc per keV

    #pick a narrower range around the peak, at hist_width percent of energy
    bounds = hist_width * rough_adc_per_kev

    peak_energies = e_vals[ (e_vals > tl08_energy - bounds) & (e_vals < tl08_energy + bounds ) ]

    #er, we can sorta guess the energy here: lets go for 0.2 keV bins
    adc_min = tl08_energy - bounds
    adc_max = tl08_energy + bounds
    bins = np.linspace(adc_min, adc_max, (2*hist_width)/0.5)

    hist, bin_edges = np.histogram(peak_energies, bins=bins)
    bin_centers = get_bin_centers(bin_edges)

    return (hist, bin_centers)

def calibrate_tl208(energy_series, peak_energies, plotFigure=None):
    '''
    energy_series: array of energies we want to calibrate
    peak_energies: array of peaks to fit

    1.) we find the 2614 peak by looking for the tallest peak at >0.5 the max adc value
    2.) fit that peak to get a rough guess at a calibration to find other peaks with
    3.) fit each peak in peak_energies
    4.) do a linear fit to the peak centroids to find a calibration
    '''

    max_adc = np.amax(energy_series)
    min_adc = np.amin(energy_series)

    ###############################################
    #do a really rough fit to the Tl208 FEP:
    ###############################################

    #only look for hi energy peaks
    energy_hi = energy_series[ energy_series > 0.5*max_adc ]
    hist, bin_centers = get_most_prominent_peak(energy_hi, 2614.533)
    guess_e, guess_sigma, guess_area = get_gaussian_guess(hist, bin_centers)

    kev_per_adc_guess = 2614.533/guess_e
    bounds = ([0.9*guess_e, 0.5*guess_sigma, 0, 0,0,0, 0],
               [1.1*guess_e, 2*guess_sigma, 0.1, 0.75, 10/kev_per_adc_guess, 10, 5*guess_area])

    params = fit_binned(radford_peak, hist, bin_centers, [guess_e, guess_sigma, 1E-3, 0.3,2/kev_per_adc_guess,0, guess_area], bounds=bounds)
    # print(params)
    # params = fit_binned(gauss, hist, bin_centers, [guess_e, guess_sigma, guess_area])
    rough_kev_per_adc = 2614.533/params[0]

    ###############################################
    #Do a real fit to every peak in peak_energies
    ###############################################

    peak_num = len(peak_energies)
    centers = np.zeros(peak_num)
    fit_result_map = {}
    bin_size = 0.2 #keV

    if plotFigure is not None:
        plot_map = {}

    for i,energy in enumerate(peak_energies):
        window_width = 10 #keV
        window_width_in_adc = window_width/rough_kev_per_adc
        energy_in_adc = energy/rough_kev_per_adc

        peak_vals = energy_series[ (energy_series > energy_in_adc -window_width_in_adc) &
                                 (energy_series < energy_in_adc +window_width_in_adc) ]

        peak_hist, bins = np.histogram(peak_vals, bins = np.arange(energy_in_adc -window_width_in_adc,
                                                             energy_in_adc +window_width_in_adc + bin_size/rough_kev_per_adc,
                                                         bin_size/rough_kev_per_adc))
        bin_centers = get_bin_centers(bins)
        guess_e, guess_sigma, guess_area = get_gaussian_guess(peak_hist, bin_centers)

        bounds = ([0.9*guess_e, 0.5*guess_sigma, 0, 0,0,0, 0],
                   [1.1*guess_e, 2*guess_sigma, 0.1, 0.75, 10/rough_kev_per_adc, 10, 5*guess_area])
        params = fit_binned(radford_peak, peak_hist, bin_centers, [guess_e, guess_sigma, 1E-3, 0.7,5,0, guess_area], bounds=bounds)

        fit_result_map[energy] = params
        centers[i] = params[0]

        if plotFigure is not None:
          plot_map[energy] = (bin_centers, peak_hist)

    #Do a linear fit to find the calibration
    linear_cal = np.polyfit(centers, peak_energies, deg=1)

    if plotFigure is not None:
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gs

        plt.figure(plotFigure.number)
        plt.clf()

        grid = gs.GridSpec(peak_num, 3)
        ax_line = plt.subplot(grid[:, 1])
        ax_spec = plt.subplot(grid[:, 2])

        for i,energy in enumerate(peak_energies):
            ax_peak = plt.subplot(grid[i, 0])
            bin_centers, peak_hist = plot_map[energy]
            params = fit_result_map[energy]
            ax_peak.plot(bin_centers*rough_kev_per_adc, peak_hist, ls="steps-mid", color="k")
            fit = radford_peak(bin_centers, *params)
            ax_peak.plot(bin_centers*rough_kev_per_adc, fit, color="b")

        ax_peak.set_xlabel("Energy [keV]")

        ax_line.scatter(centers, peak_energies, )

        x = np.arange(0,max_adc,1)
        ax_line.plot(x, linear_cal[0]*x+linear_cal[1])
        ax_line.set_xlabel("ADC")
        ax_line.set_ylabel("Energy [keV]")

        energies_cal = energy_series * linear_cal[0] + linear_cal[1]
        peak_hist, bins = np.histogram(energies_cal, bins = np.arange(0, 2700))
        ax_spec.semilogy(get_bin_centers(bins), peak_hist, ls="steps-mid")
        ax_spec.set_xlabel("Energy [keV]")

    return linear_cal
