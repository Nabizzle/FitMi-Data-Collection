#!/usr/bin/env python

import numpy as np
import time
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

        angle_ymax = 180
        angle_ymin = -angle_ymax

        gyro_ymax = 1100
        gyro_ymin = -gyro_ymax

        acceleration_ymax = 1000
        acceleration_ymin = -acceleration_ymax

        velocity_ymax = 500
        velocity_ymin = -velocity_ymax

        load_cell_ymax = 1100
        load_cell_ymin = 0

        self.fig = plt.figure()
        self.fig.suptitle("FitMi Puck Data", fontsize = 20)
        self.fig.set_size_inches(20, 10, forward = True)
        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4, hspace=0.4)

        self.roll_plot = AniPlot(self.fig, [5, 3, 1], buffer_min, buffer_max, angle_ymin / 2, angle_ymax / 2, second_puck=True)
        self.roll_plot.set_ylabel("roll angle")
        self.pitch_plot = AniPlot(self.fig, [5, 3, 2], buffer_min, buffer_max, angle_ymin, angle_ymax, second_puck=True)
        self.pitch_plot.set_ylabel("pitch angle")
        self.yaw_plot = AniPlot(self.fig, [5, 3, 3], buffer_min, buffer_max, angle_ymin, angle_ymax, second_puck=True)
        self.yaw_plot.set_ylabel("yaw angle")

        self.x_gyro_plot = AniPlot(self.fig, [5, 3, 4], buffer_min, buffer_max, gyro_ymin, gyro_ymax, second_puck=True)
        self.x_gyro_plot.set_ylabel("x gyroscope")
        self.y_gyro_plot = AniPlot(self.fig, [5, 3, 5], buffer_min, buffer_max, gyro_ymin, gyro_ymax, second_puck=True)
        self.y_gyro_plot.set_ylabel("y gyroscope")
        self.z_gyro_plot = AniPlot(self.fig, [5, 3, 6], buffer_min, buffer_max, gyro_ymin, gyro_ymax, second_puck=True)
        self.z_gyro_plot.set_ylabel("z gyroscope")

        self.x_acceleration_plot = AniPlot(self.fig, [5, 3, 7], buffer_min, buffer_max, acceleration_ymin, acceleration_ymax, second_puck=True)
        self.x_acceleration_plot.set_ylabel("x rotational acceleration")
        self.y_acceleration_plot = AniPlot(self.fig, [5, 3, 8], buffer_min, buffer_max, acceleration_ymin, acceleration_ymax, second_puck=True)
        self.y_acceleration_plot.set_ylabel("y rotational acceleration")
        self.z_acceleration_plot = AniPlot(self.fig, [5, 3, 9], buffer_min, buffer_max, acceleration_ymin, acceleration_ymax, second_puck=True)
        self.z_acceleration_plot.set_ylabel("z rotational acceleration")

        self.x_velocity_plot = AniPlot(self.fig, [5, 3, 10], buffer_min, buffer_max, velocity_ymin, velocity_ymax, second_puck=True)
        self.x_velocity_plot.set_ylabel("x velocity")
        self.y_velocity_plot = AniPlot(self.fig, [5, 3, 11], buffer_min, buffer_max, velocity_ymin, velocity_ymax, second_puck=True)
        self.y_velocity_plot.set_ylabel("y velocity")
        self.z_velocity_plot = AniPlot(self.fig, [5, 3, 12], buffer_min, buffer_max, velocity_ymin, velocity_ymax, second_puck=True)
        self.z_velocity_plot.set_ylabel("z velocity")

        self.load_cell_plot = AniPlot(self.fig, [5, 1, 5], buffer_min, buffer_max, ymin=load_cell_ymin, ymax=load_cell_ymax, second_puck=True)
        self.load_cell_plot.set_ylabel("load cell")

        self.fig.align_ylabels(self.fig.axes)
        self.fig.canvas.draw()

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
            time.sleep(1.0/self.fs)
            tick_up+=1
            if tick_up > self.fs:
                tick_up=0

    def stop(self):
        self.puck.sendCommand(0,SENDVEL, 0x00, 0x00)
        self.puck.sendCommand(1,SENDVEL, 0x00, 0x00)
        self.puck.close()

    def run(self, puck_data=None, puck_data2=None):
        # update the xy data
        self.update_buffers(puck_data, puck_data2)

        self.roll_plot.draw(self.fig)
        self.pitch_plot.draw(self.fig)
        self.yaw_plot.draw(self.fig)

        self.x_gyro_plot.draw(self.fig)
        self.y_gyro_plot.draw(self.fig)
        self.z_gyro_plot.draw(self.fig)

        self.x_acceleration_plot.draw(self.fig)
        self.y_acceleration_plot.draw(self.fig)
        self.z_acceleration_plot.draw(self.fig)

        self.x_velocity_plot.draw(self.fig)
        self.y_velocity_plot.draw(self.fig)
        self.z_velocity_plot.draw(self.fig)

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
        self.roll_plot.update(puck_data.rpy[0,0], puck_data2.rpy[0,0])
        self.pitch_plot.update(puck_data.rpy[0,1], puck_data2.rpy[0,1])
        self.yaw_plot.update(puck_data.rpy[0,2], puck_data2.rpy[0,2])

        self.x_gyro_plot.update(puck_data.gyroscope[0,0], puck_data2.gyroscope[0,0])
        self.y_gyro_plot.update(puck_data.gyroscope[0,1], puck_data2.gyroscope[0,1])
        self.z_gyro_plot.update(puck_data.gyroscope[0,2], puck_data2.gyroscope[0,2])

        self.x_acceleration_plot.update(puck_data.accelerometer[0,0], puck_data2.accelerometer[0,0])
        self.y_acceleration_plot.update(puck_data.accelerometer[0,1], puck_data2.accelerometer[0,1])
        self.z_acceleration_plot.update(puck_data.accelerometer[0,2], puck_data2.accelerometer[0,2])

        self.x_velocity_plot.update(puck_data.velocity[0,0], puck_data2.velocity[0,0])
        self.y_velocity_plot.update(puck_data.velocity[0,1], puck_data2.velocity[0,1])
        self.z_velocity_plot.update(puck_data.velocity[0,2], puck_data2.velocity[0,2])
        
        self.load_cell_plot.update(puck_data.load_cell, puck_data2.load_cell)

        if np.linalg.norm(puck_data2.accelerometer) > 1500:
            self.puck.actuate(1, 500, 100)

if __name__ == '__main__':
    plotter = PuckPlotter()
    try:
        plotter.start()
    finally:
        plotter.stop()
