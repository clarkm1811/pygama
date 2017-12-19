import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs

from .peak_fitting import *

def get_ae_cut(e_cal, current, plotFigure=None):
    #try to get a rough A/E cut

    #DEP range and nearby BG for BG subtraction
    dep_idxs =  (e_cal > 1585) & (e_cal < 1595 )   #(asymmetric around 1592 to account for CT)
    bg_idxs =  (e_cal > 1560) & (e_cal < 1570 )

    #SEP range and nearby BG for BG subtraction
    sep_idxs =  (e_cal > 2090) & (e_cal < 2115 )
    bg_sep_idxs =  (e_cal > 2060) & (e_cal < 2080 )

    a_over_e = current / e_cal

    h_dep,bins  = np.histogram(a_over_e[dep_idxs] , bins=1000)
    h_bg,bins  = np.histogram( a_over_e[bg_idxs], bins=bins)
    bin_centers = bins[:-1] + 0.5*(bins[1] - bins[0])
    h_bgs = h_dep - h_bg

    h_sep,bins  = np.histogram( a_over_e[sep_idxs], bins=bins)
    h_sepbg,bins  = np.histogram( a_over_e[bg_sep_idxs], bins=bins)
    h_bgs_sep = h_sep - h_sepbg

    p0 = get_gaussian_guess(h_bgs, bin_centers)
    p = fit_binned(gauss, h_bgs, bin_centers, p0)
    fit = gauss(bin_centers, *p)
    ae_cut = p[0] - 1.28 * p[1] #cuts at 10% of CDF

    if plotFigure is not None:
        ####
        # Plot A/E distributions
        ###
        plt.figure(plotFigure.number)
        plt.clf()
        grid = gs.GridSpec(2, 2)

        ax_dep = plt.subplot(grid[0, 0])
        ax_sep = plt.subplot(grid[1, 0])
        ax_ae = plt.subplot(grid[:, 1])

        ax_ae.plot(bin_centers,h_bgs / np.sum(h_bgs),  ls="steps-mid", color = "b", label = "DEP (BG subtracted)")
        ax_ae.plot(bin_centers, h_bgs_sep/ np.sum(h_bgs), ls="steps-mid", color = "g", label = "SEP (BG subtracted)")
        # plt.plot(bin_centers, fit, color="g")
        ax_ae.axvline(ae_cut, color="r", ls=":")
        ax_ae.legend(loc=2)

        ax_ae.set_xlabel("A/E value [arb]")

        ###
        # Plot SEP/DEP before/after cut
        ##
        ae_cut_idxs = a_over_e > ae_cut
        e_cal_aepass = e_cal[ae_cut_idxs]

        pad = 50
        bins = np.linspace(1592-pad, 1592+pad, 2*pad+1)

        ax_dep.hist( e_cal[(e_cal > 1592-pad) & (e_cal < 1592+pad )] ,  histtype="step", color = "k", label="DEP", bins=bins)
        ax_dep.hist( e_cal_aepass[(e_cal_aepass > 1592-pad) & (e_cal_aepass < 1592+pad )] ,  histtype="step", color = "b", label="After Cut", bins=bins)
        ax_dep.legend(loc=2)
        ax_dep.set_xlabel("Energy [keV]")

        bins = np.linspace(2103-pad, 2103+pad, 2*pad+1)
        ax_sep.hist( e_cal[(e_cal > 2103-pad) & (e_cal < 2103+pad )] ,  histtype="step", color = "k", label="SEP", bins=bins)
        ax_sep.hist( e_cal_aepass[(e_cal_aepass > 2103-pad) & (e_cal_aepass < 2103+pad )] ,  histtype="step", color = "b", label="After Cut", bins=bins)
        ax_sep.legend(loc=2)
        ax_sep.set_xlabel("Energy [keV]")

    return ae_cut
