import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs

from .peak_fitting import *

def gaussian_cut(data, cut_sigma=3,plotFigure=None):
    '''
    fits data to a gaussian, returns mean +/- cut_sigma values for a cut
    '''

    nbins = 100

    median = np.median(data)
    width = (np.percentile(data, 80) - np.percentile(data, 20))

    good_data = data[(data > (median - 4*width)) & (data < (median + 4*width))]

    hist, bins = np.histogram(good_data, bins=101)#np.linspace(1,5,101)
    bin_centers = bins[:-1] + (bins[1] - bins[0])/2

    #fit gaussians to that
    # result = fit_unbinned(gauss, hist, [median, width/2] )
    # print("unbinned: {}".format(result))

    result = fit_binned(gauss, hist, bin_centers, [median, width/2, np.amax(hist)*(width/2)*np.sqrt(2*np.pi)] )
    # print("binned: {}".format(result))
    cut_lo = result[0]-cut_sigma*result[1]
    cut_hi = result[0]+cut_sigma*result[1]

    if plotFigure is not None:
        plt.figure(plotFigure.number)
        plt.plot(bin_centers,hist, ls="steps-mid", color="k", label="data")
        fit = gauss(bin_centers,*result)
        plt.plot(bin_centers, fit, label="gaussian fit")
        plt.axvline(result[0], color = "g", label="fit mean")
        plt.axvline(cut_lo, color = "r", label = "+/- {} sigma".format(cut_sigma) )
        plt.axvline(cut_hi, color = "r")
        plt.legend()
        # plt.xlabel(params[i])

    return cut_lo, cut_hi

def xtalball_cut(data, cut_sigma=3,plotFigure=None):
    '''
    fits data to a crystalball, returns mean +/- cut_sigma values for a cut
    '''

    nbins = 100

    median = np.median(data)
    width = (np.percentile(data, 80) - np.percentile(data, 20))

    good_data = data[(data > (median - 4*width)) & (data < (median + 4*width))]

    hist, bins = np.histogram(good_data, bins=101)#np.linspace(1,5,101)
    bin_centers = bins[:-1] + (bins[1] - bins[0])/2

    #fit gaussians to that
    # result = fit_unbinned(gauss, hist, [median, width/2] )
    # print("unbinned: {}".format(result))
    p0 = get_gaussian_guess(hist, bin_centers)
    bounds = [(p0[0]*.5, p0[1]*.5,p0[2]*.2,0,1),
              (p0[0]*1.5, p0[1]*1.5, p0[2]*5, np.inf, np.inf)]
    result = fit_binned(xtalball, hist, bin_centers, [p0[0], p0[1], p0[2],10,1], bounds=bounds )
    # print("binned: {}".format(result))
    cut_lo = result[0]-cut_sigma*result[1]
    cut_hi = result[0]+cut_sigma*result[1]

    if plotFigure is not None:
        plt.figure(plotFigure.number)
        plt.plot(bin_centers,hist, ls="steps-mid", color="k", label="data")
        fit = xtalball(bin_centers,*result)
        plt.plot(bin_centers, fit, label="xtalball fit")
        plt.axvline(result[0], color = "g", label="fit mean")
        plt.axvline(cut_lo, color = "r", label = "+/- {} sigma".format(cut_sigma) )
        plt.axvline(cut_hi, color = "r")
        plt.legend()
        # plt.xlabel(params[i])

    return cut_lo, cut_hi
