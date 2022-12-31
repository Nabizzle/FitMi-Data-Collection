'''
Helper functions for working with quaternions

Functions to help with using quaternions when rotating a point around the
global reference frame.

Functions
---------
q_normalize(q)
    Normalizes a quaternion by its magnitude
q_multiply(q1, q2)
    Multiply two quaternions by each other
q_conjugate(q):
    Get the conjugate of a quaternion
q_rotate_vector(q, v)
    Use a quaternion to rotate a vector
'''
import numpy as np

def q_normalize(q):
    '''
    Normalizes a quaternion by its magnitude

    Parameters
    ----------
    q : numpy array
        An input quaternion

    Returns
    -------
    numpy array
        The input quaternion normalized
    '''
    return q / np.linalg.norm(q)

def q_multiply(q1, q2):
    '''
    Multiply two quaternions by each other

    Parameters
    ----------
    q1 : numpy array
        The left multiplied quaternion
    q2 : numpy array
        The right multiplied quaternion

    Returns
    -------
    numpy array
        The product of the two input quaternions
    '''
    # extract out the constants of the quaternions
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2

    # Apply the predefined multiplication
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
    z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2

    return np.array([w, x, y, z])

def q_conjugate(q):
    '''
    Get the conjugate of a quaternion

    Parameters
    ----------
    q : numpy array
        Input quaternion

    Returns
    -------
    numpy array
        The conjugate of the input quaternion
    '''
    w, x, y, z = q
    return np.array([w, -x, -y, -z])

def q_rotate_vector(q, v):
    '''
    Use a quaternion to rotate a vector

    Convert a vector to a pure quaternion apply a quaternion rotation

    Parameters
    ----------
    q : numpy array
        An input quaternion
    v : numpy array
        An input vector

    Returns
    -------
    numpy array
        The rotated vector

    '''
    q_v = np.insert(v, 0,0) # make the vector into a pure quaternion

    # rotate the vector by left multiplying it by the quaternion and right
    # multiplying it by the conjugate of the quaternion. Return only the vector
    # part of the new quaternion
    return q_multiply(q_multiply(q, q_v), q_conjugate(q))[1:]

if __name__ == "__main__":
    '''
    Demonstrate quaternion rotation by rotating a unit vector along the z axis
    '''
    q1 = q_normalize(np.array([np.pi/4.0, 0, 1, 0] ))
    v1 = np.array([0,0,1])
    print(q_rotate_vector(q1, v1))
