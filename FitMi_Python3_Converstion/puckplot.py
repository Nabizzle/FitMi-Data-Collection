#!/usr/bin/env python

import numpy as np
import time
import matplotlib
from matplotlib import pyplot as plt
from ani_plot import AniPlot

from Puck import HIDPuckDongle
from Puck.hid_puck import *

class PuckPlotter(object):
    def __init__(self):
        self.fs = 60
        self.n_seconds = 100
        self.max_samples = self.fs*self.n_seconds
        buffer_min = 0
        buffer_max = 200

        ymax = 180
        ymin = -180

        self.fig = plt.figure()
        self.fig.set_size_inches(6, 10, forward=True)
        self.plot_1 = AniPlot(self.fig, 411, buffer_min, buffer_max,
                                            ymin, ymax, double=True)

        self.plot_2 = AniPlot(self.fig, 412, buffer_min, buffer_max,
                                            -500, 500, double=True)

        self.plot_3 = AniPlot(self.fig, 413, buffer_min, buffer_max,
                                            -1000, 1000, double=True)

        self.load_cell_plot = AniPlot(self.fig, 414, buffer_min, buffer_max,
                                        ymin=-100, ymax=1100, double=True)
        self.load_cell_plot_red = False
        self.time = 0
        self.puck = HIDPuckDongle()
        self.plot_1.set_ylabel("vert angle")
        self.plot_2.set_ylabel("gyro x")
        self.plot_3.set_ylabel("accel x")
        self.load_cell_plot.set_ylabel("load cell")

    def start(self):
        self.puck.open()
        self.puck.sendCommand(0,SENDVEL, 0x00, 0x01)
        self.puck.sendCommand(1,SENDVEL, 0x00, 0x01)
        #self.puck.setTouchBuzz(1,0)
        tick_up = 0
        for i in range(0, 10000):
            self.puck.checkForNewPuckData()
            self.run(self.puck.puck_packet_0, self.puck.puck_packet_1)
            # print "connected ", self.puck.puck_packet_0.connected, self.puck.puck_packet_1.connected
            #print "pipes ", self.puck.block0_pipe, self.puck.block1_pipe
            time.sleep(1.0/self.fs)
            tick_up+=1
            if tick_up > self.fs:
                tick_up=0
                #print".",

    def stop(self):
        self.puck.sendCommand(0,SENDVEL, 0x00, 0x00)
        self.puck.sendCommand(1,SENDVEL, 0x00, 0x00)
        #self.puck.setTouchBuzz(1,1)
        self.puck.close()

    def run(self, puck_data=None, puck_data2=None):
        # update the xy data
        self.update_buffers(puck_data, puck_data2)

        self.plot_1.draw(self.fig)
        self.plot_2.draw(self.fig)
        self.plot_3.draw(self.fig)
        self.load_cell_plot.draw(self.fig)

        if puck_data.touch:
            self.load_cell_plot.plt.set_color("r")
        else:
            self.load_cell_plot.plt.set_color("b")

        if puck_data2.touch and self.load_cell_plot.plt2:
            self.load_cell_plot.plt2.set_color("r")
        else:
            self.load_cell_plot.plt2.set_color("b")

    ##---- the real update function ------------------------------------------##
    def update_buffers(self, puck_data, puck_data2):
        self.plot_1.update(puck_data.getVertAngle(), puck_data2.getVertAngle())
        self.plot_2.update(puck_data.gyroscope[0,0], puck_data2.gyroscope[0,0])
        self.plot_3.update(puck_data.accelerometer[0,0], puck_data2.accelerometer[0,0])
        self.load_cell_plot.update(puck_data.load_cell, puck_data2.load_cell)
        puck_data.getVertAngle()

        if np.linalg.norm(puck_data2.accelerometer) > 1500:
            self.puck.actuate(1, 500, 100)
        #self.puck.sendCommand(0, RBLINK, 0x01, 0x21)
        #print(puck_data.res_v5) # res_v5 is currently set up to tell us if in gaming state

if __name__ == '__main__':
    plotter = PuckPlotter()
    try:
        plotter.start()
    finally:
        plotter.stop()
    #for i in range(0, 500):
    #    plotter.run()
