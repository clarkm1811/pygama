import numpy as np
from scipy import signal


def rc_decay(rc1_us, freq = 100E6):
    rc1_dig= 1E-6 * (rc1_us) * freq
    rc1_exp = np.exp(-1./rc1_dig)
    num = [1,-1]
    den = [1, -rc1_exp]

    return (num, den)
