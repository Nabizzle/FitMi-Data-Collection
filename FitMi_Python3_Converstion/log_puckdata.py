##----------------------------------------------------------------------------##
##---- log puck data ---------------------------------------------------------##
##----------------------------------------------------------------------------##
## This will log puck data to a file. it saves the file as a python dictionary
## and also as a .mat file.

import os
import shelve
import numpy as np
from scipy import io
import threading
from Puck.hid_puck import *

class PuckLogger(object):
    ##---- initialize the puck logger ----------------------------------------##
    def __init__(self):
        self.datafolder = os.path.join(os.getcwd(), "data")
        self.fname = "default"

        self.fs = 50.0 # 50 samples per second.
        self.keep_running = True
        self.puck = HIDPuckDongle()

        self.current_samp = 0
        self.n_samples = None
        self.p0_xl = None
        self.p0_gy = None
        self.p0_mag = None
        self.p0_loadcell = None
        self.p0_quat = None

        self.p1_xl = None
        self.p1_gy = None
        self.p1_mag = None
        self.p1_loadcell = None
        self.p1_quat = None

        self.checkstop_thread = threading.Thread(target=self.check_stop)
        self.checkstop_thread.daemon = True

    ##---- check if we want to pause the recording ---------------------------##
    def check_stop(self):
        while self.keep_running:
            response = raw_input("press enter to stop logging.")
            self.keep_running = False

    ##---- run ---------------------------------------------------------------##
    def run(self):
        self.set_recording_length()
        self.set_filename()
        self.puck.open()
        self.puck.sendCommand(0,SENDVEL, 0x00, 0x00)
        self.puck.sendCommand(1,SENDVEL, 0x00, 0x00)

        print "recording data"
        self.checkstop_thread.start()
        self.current_samp = 0
        while self.keep_running and (self.current_samp < self.n_samples):
            self.puck.checkForNewPuckData()
            self.store_data(self.puck.puck_packet_0, self.puck.puck_packet_1)
            time.sleep(1.0/self.fs)

        ## crop away any unused space.
        if self.current_samp < self.n_samples:
            self.p0_xl = self.p0_xl[self.current_samp, :]
            self.p0_gy = self.p0_gy[self.current_samp, :]
            self.p0_mag = self.p0_mag[self.current_samp, :]
            self.p0_loadcell = self.p0_loadcell[self.current_samp, :]
            self.p0_quat = self.p0_quat[self.current_samp, :]
            self.p1_xl = self.p1_xl[self.current_samp, :]
            self.p1_gy = self.p1_gy[self.current_samp, :]
            self.p1_mag = self.p1_mag[self.current_samp, :]
            self.p1_loadcell = self.p1_loadcell[self.current_samp, :]
            self.p1_quat = self.p1_quat[self.current_samp, :]

    ##---- set filename ------------------------------------------------------##
    def set_filename(self):
        self.fname = raw_input("enter a name for the datafile: ")

    ##---- set recording length ----------------------------------------------##
    def set_recording_length(self):
        gotdata = False
        message = "how long would you like to record (in minutes)? "
        n_minutes = -1
        while not gotdata:
            try:
                n_minutes = float(raw_input(message))
                gotdata = True
            except:
                print "you need to input a number"

        if (n_minutes > 60) or (n_minutes < 0):
            print "please enter a number between 0 and 60"
            self.set_recording_length()
            return

        n_samples = int(n_minutes*60*self.fs)
        self.n_samples = n_samples
        self.p0_xl = np.zeros([n_samples, 3])
        self.p0_gy = np.zeros([n_samples, 3])
        self.p0_mag = np.zeros([n_samples, 3])
        self.p0_loadcell = np.zeros([n_samples, 1])
        self.p0_quat = np.zeros([n_samples, 4])
        self.p1_xl = np.zeros([n_samples, 3])
        self.p1_gy = np.zeros([n_samples, 3])
        self.p1_mag = np.zeros([n_samples, 3])
        self.p1_loadcell = np.zeros([n_samples, 1])
        self.p1_quat = np.zeros([n_samples, 4])

    ##---- write data line ---------------------------------------------------##
    def store_data(self, ppack0, ppack1):
        self.p0_xl[self.current_samp, :] = ppack0.accel
        self.p0_gy[self.current_samp, :] = ppack0.gyro
        self.p0_mag[self.current_samp, :] = ppack0.magnetometer
        self.p0_loadcell[self.current_samp, :] = ppack0.loadcell
        self.p0_quat[self.current_samp, :] = ppack0.quat

        self.p1_xl[self.current_samp, :] = ppack1.accel
        self.p1_gy[self.current_samp, :] = ppack1.gyro
        self.p1_mag[self.current_samp, :] = ppack1.magnetometer
        self.p1_loadcell[self.current_samp, :] = ppack1.loadcell
        self.p1_quat[self.current_samp, :] = ppack1.quat
        self.current_samp += 1

    ##---- write data to files -----------------------------------------------##
    def write_data(self):
        ddict = {
            "p0_xl": self.p0_xl, "p0_gy": self.p0_gy, "p0_mag": self.p0_mag,
            "p0_loadcell": self.p0_loadcell, "p0_quat": self.p0_quat,
            "p1_xl": self.p1_xl, "p1_gy": self.p1_gy, "p1_mag": self.p1_mag,
            "p1_loadcell": self.p1_loadcell, "p1_quat": self.p1_quat
            }
        shelvename = os.path.join(self.datafolder, self.fname+".shelve")
        datash = shelve.open(shelvename)
        for key in ddict.keys():
            datash[key] = ddict[key]
        datash.close()

        matpath = os.path.join(self.datafolder, self.fname+".mat")
        io.savemat(matpath, ddict, appendmat=False)

    ##---- stop communication with the pucks ---------------------------------##
    def stop(self):
        self.puck.sendCommand(0,SENDVEL, 0x00, 0x00)
        self.puck.sendCommand(1,SENDVEL, 0x00, 0x00)
        #self.puck.setTouchBuzz(1,1)
        self.puck.close()
        self.write_data()
        try:
            self.checkstop_thread.join(2)
        except:
            pass

if __name__ == "__main__":
    plogger = PuckLogger()
    try:
        plogger.run()
    finally:
        plogger.stop()
