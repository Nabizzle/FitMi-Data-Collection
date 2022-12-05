##----------------------------------------------------------------------------##
##---- Rehab puck data packet ------------------------------------------------##
##----------------------------------------------------------------------------##

import struct
import numpy as np
from Quaternion import qv_mult
import math

##---- Puck Packet -----------------------------------------------------------##
class PuckPacket(object):
    def __init__(self):
        self.accel = np.matrix([0,0,0])
        self.gyro = np.matrix([0,0,0])
        self.magnetometer = np.matrix([0,0,0])
        self.velocity = np.matrix([0,0,0])   #linear velocity in global ref - only updates if activated.
        self.quat = np.array([0,0,0,0])
        self.rpy = np.matrix([0,0,0])
        self.loadcell = 0
        self.battery = 0
        self.charging = 0
        self.connected = 0
        self.touch = 0
        self.imuok = 0
        self.velmd = 0
        self.state = 0
        self.resv5 = 0

        self.packet_def = self.create_package_definition()

    ##---- Define the structure of the packet --------------------------------##
    def create_package_definition(self):
        # note: I'm combining them this way for readability - this could just be one string
        accel = "hhh"
        gyro  = "hhh"
        magnt = "hhh"
        quat   = "hhhh"
        loadcell = "h"
        battery  = "B"
        status   = "B"
        return "<"+accel+gyro+magnt+quat+loadcell+battery+status

    ##---- parse a data packet -----------------------------------------------##
    def parse(self, raw_data):
        data = struct.unpack(self.packet_def, raw_data)
        self.accel[0:2] = data[0:3]
        self.gyro[0:2] = data[3:6]
        vel_or_mag = data[6:9]
        self.quat[0:4] = data[9:13]
        self.quat = self.quat / 10000.0 # we multiplied the float by 10000 before converting to an int16
        self.loadcell = data[13]
        self.battery = data[14]
        self.parse_status(data[15])

        # if "send velocity" is enabled, update velocity. else update magnetometer
        if (self.velmd):
            self.velocity[0:2] = vel_or_mag
        else:
            self.magnetometer[0:2] = vel_or_mag
            self.magnetometer = self.magnetometer / 100.0 # Must be done this way to make the mac happy. Likely a numpy version difference
            #self.magnetometer/=100.0
        self.get_rpy() # gets rpy angles from quaternion

    ##---- parse the status byte of the data packet --------------------------##
    def parse_status(self, status):
        self.connected = (status & 0b00000001)
        self.imuok =     (status & 0b00000010) >> 1
        self.touch =     (status & 0b00000100) >> 2
        self.velmd =     (status & 0b00001000) >> 3
        self.state =     (status & 0b01110000) >> 4
        self.resv5 =     (status & 0b10000000) >> 7

    ##---- get rpy angles from quaternion ------------------------------------##
    def get_rpy(self):
        q0 = self.quat[0]
        q1 = self.quat[1]
        q2 = self.quat[2]
        q3 = self.quat[3]
        #print "%s, %s, %s, %s" % (q0, q1, q2, q3)
        self.rpy[0,2] = np.arctan2(2.0 * (q1 * q2 + q0 * q3), q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3)*180.0/np.pi
        self.rpy[0,1] = -np.arcsin(2.0 * (q1 * q3 - q0 * q2))*180.0/np.pi
        self.rpy[0,0]  = np.arctan2(2.0 * (q0 * q1 + q2 * q3), q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3)*180.0/np.pi

    def getVertAngle(self):
        # rotate the z unit vector by our quaternion.
        v1 = np.array([0,0,1])
        vt = qv_mult(self.quat, v1)
        return np.arccos(np.linalg.norm(vt[0:2]))*180.0/np.pi * np.sign(vt[2])

    def getZAngle(self):
        # rotate the z unit vector by our quaternion.
        v1 = np.array([0.0,0.0,1.0])
        vt = qv_mult(self.quat, v1)
        nvt = np.linalg.norm(vt)
        if nvt > 0:
            vt = vt / nvt
        #print np.arccos(np.linalg.norm(vt[0:2]))*180.0/np.pi * np.sign(vt[2])
        ZAngle = np.arccos(np.linalg.norm(vt[0:2]))*180.0/np.pi * np.sign(vt[2])
        #val = vt
        if math.isnan(ZAngle):
            return None
        else:
            return ZAngle
            
    def getXAngle(self):
        # rotate the z unit vector by our quaternion.
        v1 = np.array([1.0,0.0,0.0])
        vt = qv_mult(self.quat, v1)
        nvt = np.linalg.norm(vt)
        if nvt > 0:
            vt = vt / nvt
        #print np.arccos(np.linalg.norm(vt[0:2]))*180.0/np.pi * np.sign(vt[2])
        XAngle = np.arccos(np.linalg.norm(vt[0:2]))*180.0/np.pi * np.sign(vt[2])
        #print int(XAngle)
        #val = vt
        if math.isnan(XAngle):
            return None
        else:
            return XAngle
            
    def getYAngle(self):
        # rotate the z unit vector by our quaternion.
        v1 = np.array([0.0,1.0,0.0])
        vt = qv_mult(self.quat, v1)
        nvt = np.linalg.norm(vt)
        if nvt > 0:
            vt = vt / nvt
        #print np.arccos(np.linalg.norm(vt[0:2]))*180.0/np.pi * np.sign(vt[2])
        XAngle = np.arccos(np.linalg.norm(vt[0:2]))*180.0/np.pi * np.sign(vt[2])
        #print int(XAngle)
        #val = vt
        if math.isnan(XAngle):
            return None
        else:
            return XAngle

    def __str__(self):
        f = (self.accel, self.gyro, self.magnetometer, self.quat, self.loadcell,
            self.battery, self.charging, self.connected,
             self.touch, self.imuok)
        return "acc: %s, gy: %s, mg: %s, quat: %s, lc: %s, bat: %s, chg: %s, cnct: %s, tch: %s, imuok: %s" % f
