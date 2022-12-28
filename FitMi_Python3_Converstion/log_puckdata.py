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
        self.data_folder = os.path.join(os.getcwd(), "data")
        self.fname = "default"

        self.fs = 50.0 # 50 samples per second.
        self.keep_running = True
        self.puck = HIDPuckDongle()

        self.current_sample = 0
        self.n_samples = None
        self.puck_0_xl = None
        self.puck_0_gyroscope = None
        self.puck_0_magnetometer = None
        self.puck_0_load_cell = None
        self.puck_0_quaternion = None

        self.puck_1_xl = None
        self.puck_1_gyroscope = None
        self.puck_1_magnetometer = None
        self.puck_1_load_cell = None
        self.puck_1_quaternion = None

        self.check_stop_thread = threading.Thread(target=self.check_stop)
        self.check_stop_thread.daemon = True

    ##---- check if we want to pause the recording ---------------------------##
    def check_stop(self):
        while self.keep_running:
            response = input("press enter to stop logging.")
            self.keep_running = False

    ##---- run ---------------------------------------------------------------##
    def run(self):
        self.set_recording_length()
        self.set_filename()
        self.puck.open()
        self.puck.sendCommand(0,SENDVEL, 0x00, 0x00)
        self.puck.sendCommand(1,SENDVEL, 0x00, 0x00)

        print("recording data")
        self.check_stop_thread.start()
        self.current_sample = 0
        while self.keep_running and (self.current_sample < self.n_samples):
            self.puck.checkForNewPuckData()
            self.store_data(self.puck.puck_packet_0, self.puck.puck_packet_1)
            time.sleep(1.0/self.fs)

        ## crop away any unused space.
        if self.current_sample < self.n_samples:
            self.puck_0_xl = self.puck_0_xl[self.current_sample, :]
            self.puck_0_gyroscope = self.puck_0_gyroscope[self.current_sample, :]
            self.puck_0_magnetometer = self.puck_0_magnetometer[self.current_sample, :]
            self.puck_0_load_cell = self.puck_0_load_cell[self.current_sample, :]
            self.puck_0_quaternion = self.puck_0_quaternion[self.current_sample, :]
            self.puck_1_xl = self.puck_1_xl[self.current_sample, :]
            self.puck_1_gyroscope = self.puck_1_gyroscope[self.current_sample, :]
            self.puck_1_magnetometer = self.puck_1_magnetometer[self.current_sample, :]
            self.puck_1_load_cell = self.puck_1_load_cell[self.current_sample, :]
            self.puck_1_quaternion = self.puck_1_quaternion[self.current_sample, :]

    ##---- set filename ------------------------------------------------------##
    def set_filename(self):
        self.fname = input("enter a name for the datafile: ")

    ##---- set recording length ----------------------------------------------##
    def set_recording_length(self):
        got_data = False
        message = "how long would you like to record (in minutes)? "
        n_minutes = -1
        while not got_data:
            try:
                n_minutes = float(input(message))
                got_data = True
            except:
                print("you need to input a number")

        if (n_minutes > 60) or (n_minutes < 0):
            print("please enter a number between 0 and 60")
            self.set_recording_length()
            return

        n_samples = int(n_minutes*60*self.fs)
        self.n_samples = n_samples
        self.puck_0_xl = np.zeros([n_samples, 3])
        self.puck_0_gyroscope = np.zeros([n_samples, 3])
        self.puck_0_magnetometer = np.zeros([n_samples, 3])
        self.puck_0_load_cell = np.zeros([n_samples, 1])
        self.puck_0_quaternion = np.zeros([n_samples, 4])
        self.puck_1_xl = np.zeros([n_samples, 3])
        self.puck_1_gyroscope = np.zeros([n_samples, 3])
        self.puck_1_magnetometer = np.zeros([n_samples, 3])
        self.puck_1_load_cell = np.zeros([n_samples, 1])
        self.puck_1_quaternion = np.zeros([n_samples, 4])

    ##---- write data line ---------------------------------------------------##
    def store_data(self, puck_packet_0, puck_packet_1):
        self.puck_0_xl[self.current_sample, :] = puck_packet_0.accelerometer
        self.puck_0_gyroscope[self.current_sample, :] = puck_packet_0.gyroscope
        self.puck_0_magnetometer[self.current_sample, :] = puck_packet_0.magnetometer
        self.puck_0_load_cell[self.current_sample, :] = puck_packet_0.load_cell
        self.puck_0_quaternion[self.current_sample, :] = puck_packet_0.quaternion

        self.puck_1_xl[self.current_sample, :] = puck_packet_1.accelerometer
        self.puck_1_gyroscope[self.current_sample, :] = puck_packet_1.gyroscope
        self.puck_1_magnetometer[self.current_sample, :] = puck_packet_1.magnetometer
        self.puck_1_load_cell[self.current_sample, :] = puck_packet_1.load_cell
        self.puck_1_quaternion[self.current_sample, :] = puck_packet_1.quaternion
        self.current_sample += 1

    ##---- write data to files -----------------------------------------------##
    def write_data(self):
        data_dictionary = {
            "puck_0_xl": self.puck_0_xl, "p0_gyroscope": self.puck_0_gyroscope, "p0_magnetometer": self.puck_0_magnetometer,
            "p0_load_cell": self.puck_0_load_cell, "p0_quaternion": self.puck_0_quaternion,
            "puck_1_xl": self.puck_1_xl, "p1_gyroscope": self.puck_1_gyroscope, "p1_magnetometer": self.puck_1_magnetometer,
            "p1_load_cell": self.puck_1_load_cell, "p1_quaternion": self.puck_1_quaternion
            }
        shelve_name = os.path.join(self.data_folder, self.fname+".shelve")
        data_shelve = shelve.open(shelve_name)
        for key in data_dictionary.keys():
            data_shelve[key] = data_dictionary[key]
        data_shelve.close()

        mat_path = os.path.join(self.data_folder, self.fname+".mat")
        io.savemat(mat_path, data_dictionary, appendmat=False)

    ##---- stop communication with the pucks ---------------------------------##
    def stop(self):
        self.puck.sendCommand(0,SENDVEL, 0x00, 0x00)
        self.puck.sendCommand(1,SENDVEL, 0x00, 0x00)
        #self.puck.setTouchBuzz(1,1)
        self.puck.close()
        self.write_data()
        try:
            self.check_stop_thread.join(2)
        except:
            pass

if __name__ == "__main__":
    puck_logger = PuckLogger()
    try:
        puck_logger.run()
    finally:
        puck_logger.stop()
