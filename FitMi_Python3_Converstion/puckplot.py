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
        buffmin = 0
        buffmax = 200

        ymax = 180
        ymin = -180

        self.fig = plt.figure()
        self.fig.set_size_inches(6, 10, forward=True)
        self.plt1 = AniPlot(self.fig, 411, buffmin, buffmax,
                                            ymin, ymax, double=True)

        self.plt2 = AniPlot(self.fig, 412, buffmin, buffmax,
                                            -500, 500, double=True)

        self.plt3 = AniPlot(self.fig, 413, buffmin, buffmax,
                                            -1000, 1000, double=True)

        self.lcplot = AniPlot(self.fig, 414, buffmin, buffmax,
                                        ymin=-100, ymax=1100, double=True)
        self.lcplot_red = False
        self.time = 0
        self.puck = HIDPuckDongle()
        self.plt1.set_ylabel("vert angle")
        self.plt2.set_ylabel("gyro x")
        self.plt3.set_ylabel("accel x")
        self.lcplot.set_ylabel("loadcell")

    def start(self):
        self.puck.open()
        self.puck.sendCommand(0,SENDVEL, 0x00, 0x01)
        self.puck.sendCommand(1,SENDVEL, 0x00, 0x01)
        #self.puck.setTouchBuzz(1,0)
        tickup = 0
        for i in range(0, 10000):
            self.puck.checkForNewPuckData()
            self.run(self.puck.puckpack0, self.puck.puckpack1)
            # print "connected ", self.puck.puckpack0.connected, self.puck.puckpack1.connected
            #print "pipes ", self.puck.block0_pipe, self.puck.block1_pipe
            time.sleep(1.0/self.fs)
            tickup+=1
            if tickup > self.fs:
                tickup=0
                #print".",

    def stop(self):
        self.puck.sendCommand(0,SENDVEL, 0x00, 0x00)
        self.puck.sendCommand(1,SENDVEL, 0x00, 0x00)
        #self.puck.setTouchBuzz(1,1)
        self.puck.close()

    def run(self, puckdata=None, puckdata2=None):
        # update the xy data
        self.update_buffers(puckdata, puckdata2)

        self.plt1.draw(self.fig)
        self.plt2.draw(self.fig)
        self.plt3.draw(self.fig)
        self.lcplot.draw(self.fig)

        if puckdata.touch:
            self.lcplot.plt.set_color("r")
        else:
            self.lcplot.plt.set_color("b")

        if puckdata2.touch and self.lcplot.plt2:
            self.lcplot.plt2.set_color("r")
        else:
            self.lcplot.plt2.set_color("b")

    ##---- the real update function ------------------------------------------##
    def update_buffers(self, puckdata, puckdata2):
        self.plt1.update(puckdata.getVertAngle(), puckdata2.getVertAngle())
        self.plt2.update(puckdata.gyro[0,0], puckdata2.gyro[0,0])
        self.plt3.update(puckdata.accel[0,0], puckdata2.accel[0,0])
        self.lcplot.update(puckdata.loadcell, puckdata2.loadcell)
        puckdata.getVertAngle()

        if np.linalg.norm(puckdata2.accel) > 1500:
            self.puck.actuate(1, 500, 100)
        #self.puck.sendCommand(0, RBLINK, 0x01, 0x21)
        #print puckdata.resv3 # resv3 is currently set up to tell us if in gaming state

if __name__ == '__main__':
    plotter = PuckPlotter()
    try:
        plotter.start()
    finally:
        plotter.stop()
    #for i in range(0, 500):
    #    plotter.run()
