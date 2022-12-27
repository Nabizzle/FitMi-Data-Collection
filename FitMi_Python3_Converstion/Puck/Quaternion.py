##----------------------------------------------------------------------------##
##---- A module with helper functions for dealing with quaternions -----------##
##----------------------------------------------------------------------------##

import numpy as np

##---- normalize a quaternion - note that v is an np array -------------------##
def q_normalize(v, tolerance=0.00001):
    mag2 = (v*v).sum()
    if np.abs(mag2 - 1.0) > tolerance:
        mag = np.sqrt(mag2)
        v = v/mag
    return v

##---- multiply quaternions --------------------------------------------------##
def q_mult(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
    z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2
    return np.array([w, x, y, z])

##---- get quaternion conjugate ----------------------------------------------##
def q_conjugate(q):
    w, x, y, z = q
    return np.array([w, -x, -y, -z])

##---- quaternion vector multiplcation ---------------------------------------##
def qv_mult(q1, v1):
    q2 = np.insert(v1, 0,0)
    return q_mult(q_mult(q1, q2), q_conjugate(q1))[1:]

if __name__ == "__main__":
    q1 = q_normalize(np.array([np.pi/4.0, 0, 1, 0] ))
    v1 = np.array([0,0,1])
    print qv_mult(q1, v1)
