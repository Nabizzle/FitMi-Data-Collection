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

        angle_ymax = 100
        angle_ymin = -100

        gyro_ymax = 1000
        gyro_ymin = -1000

        acceleration_ymax = 1000
        acceleration_ymin = -1000

        load_cell_ymax = 1100
        load_cell_ymin = 0

        self.fig = plt.figure()
        self.fig.set_size_inches(20, 9, forward = True)

        self.x_angle_fig_axis = self.fig.add_subplot(4, 3, 1, ylim = (angle_ymin, angle_ymax))
        self.y_angle_fig_axis = self.fig.add_subplot(4, 3, 2, ylim = (angle_ymin, angle_ymax))
        self.z_angle_fig_axis = self.fig.add_subplot(4, 3, 3,ylim = (angle_ymin, angle_ymax))

        self.gyro_x_fig_axis = self.fig.add_subplot(4, 3, 4, ylim = (gyro_ymin, gyro_ymax))
        self.gyro_y_fig_axis = self.fig.add_subplot(4, 3, 5, ylim = (gyro_ymin, gyro_ymax))
        self.gyro_z_fig_axis = self.fig.add_subplot(4, 3, 6, ylim = (gyro_ymin, gyro_ymax))

        self.acceleration_x_fig_axis = self.fig.add_subplot(4, 3, 7, ylim = (acceleration_ymin, acceleration_ymax))
        self.acceleration_y_fig_axis = self.fig.add_subplot(4, 3, 8, ylim = (acceleration_ymin, acceleration_ymax))
        self.acceleration_z_fig_axis = self.fig.add_subplot(4, 3, 9, ylim = (acceleration_ymin, acceleration_ymax))

        self.load_cell_fig_axis = self.fig.add_subplot(4, 1, 4, ylim = (load_cell_ymin, load_cell_ymax))

        self.x_angle_fig_axis.set_ylabel("x angle")
        self.y_angle_fig_axis.set_ylabel("y angle")
        self.z_angle_fig_axis.set_ylabel("z angle")

        self.gyro_x_fig_axis.set_ylabel("x gyroscope")
        self.gyro_y_fig_axis.set_ylabel("y gyroscope")
        self.gyro_z_fig_axis.set_ylabel("z gyroscope")

        self.acceleration_x_fig_axis.set_ylabel("x acceleration")
        self.acceleration_y_fig_axis.set_ylabel("y acceleration")
        self.acceleration_z_fig_axis.set_ylabel("z acceleration")
        
        self.load_cell_fig_axis.set_ylabel("load cell")

        self.x_angle_plot = AniPlot(self.fig, self.x_angle_fig_axis, buffer_min, buffer_max, angle_ymin, angle_ymax, second_puck=True)
        self.y_angle_plot = AniPlot(self.fig, self.y_angle_fig_axis, buffer_min, buffer_max, angle_ymin, angle_ymax, second_puck=True)
        self.z_angle_plot = AniPlot(self.fig, self.z_angle_fig_axis, buffer_min, buffer_max, angle_ymin, angle_ymax, second_puck=True)

        self.x_gyro_plot = AniPlot(self.fig, self.gyro_x_fig_axis, buffer_min, buffer_max, -500, 500, second_puck=True)
        self.y_gyro_plot = AniPlot(self.fig, self.gyro_y_fig_axis, buffer_min, buffer_max, -500, 500, second_puck=True)
        self.z_gyro_plot = AniPlot(self.fig, self.gyro_z_fig_axis, buffer_min, buffer_max, -500, 500, second_puck=True)

        self.x_acceleration_plot = AniPlot(self.fig, self.acceleration_x_fig_axis, buffer_min, buffer_max, -1000, 1000, second_puck=True)
        self.y_acceleration_plot = AniPlot(self.fig, self.acceleration_y_fig_axis, buffer_min, buffer_max, -1000, 1000, second_puck=True)
        self.z_acceleration_plot = AniPlot(self.fig, self.acceleration_z_fig_axis, buffer_min, buffer_max, -1000, 1000, second_puck=True)

        self.load_cell_plot = AniPlot(self.fig, self.load_cell_fig_axis, buffer_min, buffer_max, ymin=-100, ymax=1100, second_puck=True)
        self.load_cell_plot_red = False
        self.time = 0
        self.puck = HIDPuckDongle()

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

        self.x_angle_plot.draw(self.fig)
        self.y_angle_plot.draw(self.fig)
        self.z_angle_plot.draw(self.fig)

        self.x_gyro_plot.draw(self.fig)
        self.y_gyro_plot.draw(self.fig)
        self.z_gyro_plot.draw(self.fig)

        self.x_acceleration_plot.draw(self.fig)
        self.y_acceleration_plot.draw(self.fig)
        self.z_acceleration_plot.draw(self.fig)

        self.load_cell_plot.draw(self.fig)

        if puck_data.touch:
            self.load_cell_plot.puck_1_plot.set_color("r")
        else:
            self.load_cell_plot.puck_1_plot.set_color("b")

        if puck_data2.touch and self.load_cell_plot.puck_2_plot:
            self.load_cell_plot.puck_2_plot.set_color("m")
        else:
            self.load_cell_plot.puck_2_plot.set_color("g")

    ##---- the real update function ------------------------------------------##
    def update_buffers(self, puck_data, puck_data2):
        self.x_angle_plot.update(puck_data.getXAngle(), puck_data2.getXAngle())
        self.y_angle_plot.update(puck_data.getYAngle(), puck_data2.getYAngle())
        self.z_angle_plot.update(puck_data.getZAngle(), puck_data2.getZAngle())

        self.x_gyro_plot.update(puck_data.gyroscope[0,0], puck_data2.gyroscope[0,0])
        self.y_gyro_plot.update(puck_data.gyroscope[0,1], puck_data2.gyroscope[0,1])
        self.z_gyro_plot.update(puck_data.gyroscope[0,2], puck_data2.gyroscope[0,2])

        self.x_acceleration_plot.update(puck_data.accelerometer[0,0], puck_data2.accelerometer[0,0])
        self.y_acceleration_plot.update(puck_data.accelerometer[0,1], puck_data2.accelerometer[0,1])
        self.z_acceleration_plot.update(puck_data.accelerometer[0,2], puck_data2.accelerometer[0,2])

        self.load_cell_plot.update(puck_data.load_cell, puck_data2.load_cell)

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
