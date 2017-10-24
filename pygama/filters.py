import numpy as np
from scipy import signal

def rc_decay_2pole(rc1_us, rs2_us, rc1_frac, freq = 100E6):
    '''
    Returns numerator/denominator pair for a filter which _applies_ a 2-pole RC decay
    Swap the num/den to get a filter which corrects

    rc1_us: Long (~70 us) RC decay constant
    rc2_us: Short (~2 us) RC decay constant
    rc1_frac: Fractional contribution of long constant (~0.99)
    freq: sampling frequency of digitizer data (in Hz)

    A single RC filter is (z-1)/(z - exp( -1/RC )) where RC is expressed in samples
    This combines them as a linear combination into a single filter:
    H(z) = c*H_rc1(z) + (1-c)* H_rc2(z)
    '''

    #Calculate the exp(-1/RC) terms
    rc1_dig= 1E-6 * (rc1_us) * freq
    rc1_exp = np.exp(-1./rc1_dig)

    rc2_dig = 1E-6 * (rs2_us) * freq
    rc2_exp = np.exp(-1./rc2_dig)

    #algebra from the linear combo
    num_term_1 = -1*(rc1_exp*(1 - rc1_frac )  + rc2_exp*rc1_frac + 1)
    num_term_2 = rc1_exp*(1 - rc1_frac )  + rc2_exp*rc1_frac

    num = [1., num_term_1, num_term_2]
    den = [1, -(rc1_exp + rc2_exp), rc1_exp * rc2_exp ]

    return (num, den)
