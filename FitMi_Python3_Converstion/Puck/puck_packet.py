import struct
import numpy as np
from Puck.quaternion import q_rotate_vector
import math

class PuckPacket(object):
    '''
    Class containing all of the data from the puck as well as calculated data

    This class contains all of the data parsed from the puck's data stream for
    its sensors as well as status indicators and one calculated variable for
    the roll, pitch, and yaw of the puck.

    Attributes
    ----------
    accelerometer : numpy array
        The x, y, and z accelerometer values of this puck
    gyroscope : numpy array
        The x, y, and z gyroscope values of this puck
    magnetometer : numpy array
        The x, y, and z magnetometer values of this puck
    velocity : numpy array
        The x, y, and z linear velocity values of this puck
    quaternion : numpy array
        The w, x, y, and z quaternion values of this 
    roll_pitch_yaw : numpy array
        The calculated roll, pitch, and yaw angles of this puck
    load cell : int
        An integer representing the force on the face of this puck
    battery : int
        Battery percentage of this puck
    charging : int
        Indicator for if this puck is charging
    connected : int
        Status flag for if the puck is connected or not (1 or 0)
    touch : int
        Status flag for if the puck is being touched or not (1 or 0)
    imu_ok : int
        Status flag for if the imu is functioning (1 or 0)
    velocity_measured : int
        Status flag for if the linear velocity or magnetometer of the puck was
        polled for (1 or 0)
    state : int
        Three bit integer for what state the puck is in
    res_v5 : int
        Status flag for something that Nabeel does not know (1 or 0)

    Methods
    -------
    __init__()
        Initializes all data storage variables to default values
    create_packet_definition()
        Defines the incoming format of the data message
    parse(raw_data)
        Separates the incoming data into the right data variables
    parse_status(status)
        Parses final char of the data packet, the status byte
    getRollPitchYaw()
        Gets the roll, pitch, and yaw angles from quaternion constants
    getAngle(v)
        Rotates vector with puck's quaternion and finds angle with the xy plane
    getXAngle()
        Finds angle between the rotated x unit vector and the global xy plane
    getYAngle()
        Finds angle between the rotated y unit vector and the global xy plane
    getZAngle()
        Finds angle between the rotated z unit vector and the global xy plane
    __str__()
        Printed string of data variables when the class is printed
    '''
    def __init__(self):
        '''
        Initializes all data storage variables to default values

        Sets all data variables to 0 and sets up the definition of the data
        packet.
        '''
        self.accelerometer = np.array([0,0,0])
        self.gyroscope = np.array([0,0,0])
        self.magnetometer = np.array([0.0, 0.0, 0.0])
        # only updates if activated when puck connected to.
        self.velocity = np.array([0,0,0])
        self.quaternion = np.array([0.0, 0.0, 0.0, 0.0])
        self.roll_pitch_yaw = np.array([0,0,0])
        self.load_cell = 0
        self.battery = 0
        self.charging = 0
        self.connected = 0
        self.touch = 0
        self.imu_ok = 0
        self.velocity_measured = 0
        self.state = 0
        self.res_v5 = 0

        self.packet_def = self.create_packet_definition()

    def create_packet_definition(self):
        '''
        Defines the incoming format of the data message

        Defines what each part of the byte array data message will be for. The
        letters represent the format for each byte in the data message array.

        Returns
        -------
        string
            The assembled data message format
        '''
        accelerometer = "hhh" # three shorts
        gyroscope  = "hhh" # three shorts
        magnetometer = "hhh" # three shorts
        quaternion   = "hhhh" # four shorts
        load_cell = "h" # one short
        battery  = "B" # one char
        status   = "B" # one char
        return "<" + accelerometer + gyroscope + magnetometer + quaternion +\
            load_cell + battery + status

    def parse(self, raw_data):
        '''
        Separates the incoming data into the right data variables

        Separates the incoming data byte array into each variable's data. Then
        calculates the roll, pitch, and yaw angles from the quaternion values
        of the puck.

        Parameters
        ----------
        raw_data : byte array
            The incoming data message from the puck
        '''
        # Read the data based on the packet format
        data = struct.unpack(self.packet_def, raw_data)

        # Save the data from the packet into the data variables
        self.gyroscope[0:3] = data[0:3]
        self.accelerometer[0:3] = data[3:6]
        # This is either the velocity or magnetometer based on what the puck
        # was asked for
        vel_or_mag = data[6:9]

        self.quaternion[0:4] = data[9:13]
        # the quaternions from the puck are multiplied by 10000 to convert
        # their float value to an int16 so this must be converted back
        self.quaternion /= 10000.0

        self.load_cell = data[13]
        self.battery = data[14]
        # takes the last char and separates it further
        self.parse_status(data[15])

        # if velocity polling is enabled, update velocity. else update
        # magnetometer
        if (self.velocity_measured):
            self.velocity[0:3] = vel_or_mag
        else:
            self.magnetometer[0:3] = vel_or_mag
            self.magnetometer /= 100.0
        
        # calculate the roll, pitch, and yaw values. Needs to be in a try catch
        # because the yellow puck does not do this correctly
        try:
            # gets the roll, pitch and yaw angles from quaternion
            self.roll_pitch_yaw[0:3] = self.getRollPitchYaw()
        except:
            pass

    def parse_status(self, status):
        '''
        Parses final char of the data packet, the status byte

        Separates the status char into the variables for if the puck is
        connected, if the imu is functioning, if the puck is touched, if the
        velocity of the puck was asked for, the state of the puck and for
        res_v5.

        Parameters
        ----------
        status : int
            The final char of the data packet
        '''
        self.connected = (status & 0b00000001)
        self.imu_ok = (status & 0b00000010) >> 1
        self.touch = (status & 0b00000100) >> 2
        self.velocity_measured = (status & 0b00001000) >> 3
        self.state = (status & 0b01110000) >> 4
        self.res_v5 = (status & 0b10000000) >> 7

    def getRollPitchYaw(self):
        '''
        Gets the roll, pitch, and yaw angles from quaternion constants
        '''
        q0 = self.quaternion[0]
        q1 = self.quaternion[1]
        q2 = self.quaternion[2]
        q3 = self.quaternion[3]

        # roll
        self.roll_pitch_yaw[0] =\
            -np.arcsin(2.0 * (q1 * q3 - q0 * q2))*180.0/np.pi

        # pitch
        self.roll_pitch_yaw[1]  =\
            np.arctan2(2.0 * (q0 * q1 + q2 * q3),
            q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3)*180.0/np.pi

        # yaw
        self.roll_pitch_yaw[2] =\
            np.arctan2(2.0 * (q1 * q2 + q0 * q3),
            q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3)*180.0/np.pi

    def getAngle(self, v):
        '''
        Rotates vector with puck's quaternion and finds angle with the xy plane

        Parameters
        ----------
        v : numpy array
            a vector to rotate by the puck's quaternion

        Returns
        -------
        v_angle : float
            Finds the angle between the rotated vector and the xy plane. Above
            the plane is positive and below is negative.
        '''
        # rotate the vector and normalize it
        v_rotated = q_rotate_vector(self.quaternion, v)
        v_rotated /= np.linalg.norm(v_rotated)

        # Find the angle between the rotated vector and the xy plane
        v_angle =\
            np.arccos(np.linalg.norm(v_rotated[0:2]))*180.0/np.pi *\
                np.sign(v_rotated[2])

        # Return the angle if it exists
        if math.isnan(v_angle):
            return None
        else:
            return v_angle
            
    def getXAngle(self):
        '''
        Finds angle between the rotated x unit vector and the global xy plane

        Returns
        -------
        float
            The angle between the rotated x axis and the xy plane. Above the
            plane is positive and below is negative.
        '''
        x_axis = np.array([0.0,0.0,1.0])
        return self.getAngle(x_axis)
            
    def getYAngle(self):
        '''
        Finds angle between the rotated y unit vector and the global xy plane

        Returns
        -------
        float
            The angle between the rotated y axis and the xy plane. Above the plane is positive and below is negative.
        '''
        y_axis = np.array([0.0,0.0,1.0])
        return self.getAngle(y_axis)

    def getZAngle(self):
        '''
        Finds angle between the rotated z unit vector and the global xy plane

        Returns
        -------
        float
            The angle between the rotated z axis and the xy plane. Above the
            plane is positive and below is negative.
        '''
        z_axis = np.array([0.0,0.0,1.0])
        return self.getAngle(z_axis)

    def __str__(self):
        '''
        Printed string of data variables when the class is printed

        Prints all of the data from the puck labeled in the console when the
        the class object is printed.

        Returns
        -------
        output_string : string
            The extracted data with labels
        '''
        output_string = (self.accelerometer, self.gyroscope, self.magnetometer,
            self.quaternion, self.load_cell,
            self.battery, self.charging, self.connected,
            self.touch, self.imu_ok)
        return "accelerometer: %s, gyroscope: %s, magnetometer: %s,\
            velocity: %s, quaternion: %s, load cell: %s, battery: %s,\
            charging: %s, connected: %s, touch: %s, imu ok: %s" % output_string
