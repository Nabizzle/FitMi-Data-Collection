##----------------------------------------------------------------------------##
##---- Rehab puck data packet ------------------------------------------------##
##----------------------------------------------------------------------------##

import struct
import numpy as np
from Puck.Quaternion import q_vector_multiply
import math

##---- Puck Packet -----------------------------------------------------------##
class PuckPacket(object):
    def __init__(self):
        self.accelerometer = np.matrix([0,0,0])
        self.gyroscope = np.matrix([0,0,0])
        self.magnetometer = np.matrix([0,0,0])
        self.velocity = np.matrix([0,0,0]) #linear velocity in global ref - only updates if activated.
        self.quaternion = np.array([0,0,0,0])
        self.rpy = np.matrix([0,0,0])
        self.load_cell = 0
        self.battery = 0
        self.charging = 0
        self.connected = 0
        self.touch = 0
        self.imu_ok = 0
        self.velocity_md = 0
        self.state = 0
        self.res_v5 = 0

        self.packet_def = self.create_package_definition()

    ##---- Define the structure of the packet --------------------------------##
    def create_package_definition(self):
        # note: I'm combining them this way for readability - this could just be one string
        accelerometer = "hhh"
        gyroscope  = "hhh"
        magnetometer = "hhh"
        quaternion   = "hhhh"
        load_cell = "h"
        battery  = "B"
        status   = "B"
        return "<" + accelerometer + gyroscope + magnetometer + quaternion + load_cell + battery + status

    ##---- parse a data packet -----------------------------------------------##
    def parse(self, raw_data):
        data = struct.unpack(self.packet_def, raw_data)
        self.accelerometer[0:3] = data[3:6]
        self.gyroscope[0:3] = data[0:3]
        vel_or_mag = data[6:9]
        self.quaternion[0:4] = data[9:13]
        self.quaternion = self.quaternion / 10000.0 # we multiplied the float by 10000 before converting to an int16
        self.load_cell = data[13]
        self.battery = data[14]
        self.parse_status(data[15])

        # if "send velocity" is enabled, update velocity. else update magnetometer
        if (self.velocity_md):
            self.velocity[0:3] = vel_or_mag
        else:
            self.magnetometer[0:3] = vel_or_mag
            self.magnetometer /= 100.0
        try:
            self.rpy[0:3] = self.get_rpy() # gets rpy angles from quaternion
        except:
            pass

    ##---- parse the status byte of the data packet --------------------------##
    def parse_status(self, status):
        self.connected = (status & 0b00000001)
        self.imu_ok =     (status & 0b00000010) >> 1
        self.touch =     (status & 0b00000100) >> 2
        self.velocity_md =     (status & 0b00001000) >> 3
        self.state =     (status & 0b01110000) >> 4
        self.res_v5 =     (status & 0b10000000) >> 7

    ##---- get rpy angles from quaternion ------------------------------------##
    def get_rpy(self):
        q0 = self.quaternion[0]
        q1 = self.quaternion[1]
        q2 = self.quaternion[2]
        q3 = self.quaternion[3]

        self.rpy[0,2] = np.arctan2(2.0 * (q1 * q2 + q0 * q3), q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3)*180.0/np.pi
        self.rpy[0,1] = -np.arcsin(2.0 * (q1 * q3 - q0 * q2))*180.0/np.pi
        self.rpy[0,0]  = np.arctan2(2.0 * (q0 * q1 + q2 * q3), q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3)*180.0/np.pi

    def getVertAngle(self):
        # rotate the z unit vector by our quaternion.
        v1 = np.array([0,0,1])
        vt = q_vector_multiply(self.quaternion, v1)
        return np.arccos(np.linalg.norm(vt[0:2]))*180.0/np.pi * np.sign(vt[2])

    def getZAngle(self):
        # rotate the z unit vector by our quaternion.
        v1 = np.array([0.0,0.0,1.0])
        vt = q_vector_multiply(self.quaternion, v1)
        nvt = np.linalg.norm(vt)
        if nvt > 0:
            vt = vt / nvt

        ZAngle = np.arccos(np.linalg.norm(vt[0:2]))*180.0/np.pi * np.sign(vt[2])

        if math.isnan(ZAngle):
            return None
        else:
            return ZAngle
            
    def getXAngle(self):
        # rotate the z unit vector by our quaternion.
        v1 = np.array([1.0,0.0,0.0])
        vt = q_vector_multiply(self.quaternion, v1)
        nvt = np.linalg.norm(vt)
        if nvt > 0:
            vt = vt / nvt

        XAngle = np.arccos(np.linalg.norm(vt[0:2]))*180.0/np.pi * np.sign(vt[2])

        if math.isnan(XAngle):
            return None
        else:
            return XAngle
            
    def getYAngle(self):
        # rotate the z unit vector by our quaternion.
        v1 = np.array([0.0,1.0,0.0])
        vt = q_vector_multiply(self.quaternion, v1)
        nvt = np.linalg.norm(vt)
        if nvt > 0:
            vt = vt / nvt

        YAngle = np.arccos(np.linalg.norm(vt[0:2]))*180.0/np.pi * np.sign(vt[2])
 
        if math.isnan(YAngle):
            return None
        else:
            return YAngle

    def __str__(self):
        f = (self.accelerometer, self.gyroscope, self.magnetometer, self.quaternion, self.load_cell,
            self.battery, self.charging, self.connected,
             self.touch, self.imu_ok)
        return "accelerometer: %s, gyroscope: %s, magnetometer: %s, quaternion: %s, load cell: %s, battery: %s, charging: %s, connected: %s, touch: %s, imu ok: %s" % f
