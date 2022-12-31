#!/usr/bin/env python

import numpy as np
import time
from matplotlib import pyplot as plt
from ani_plot import AniPlot
from Puck.hid_puck import HIDPuckDongle
from Puck.hid_puck import *

class PuckPlotter(object):
    '''
    This class plots data from the FitMi pucks

    A PuckPlotter shows a window of time of raw and processed data for
    visualization and debugging purposes. One or both pucks can be used and
    this class is good for demonstrating that data the pucks give the user.

    Attributes
    ----------
    samples_per_second : int
        The number of times the pucks are queried per second
    max_run_time_seconds : int
        Total amount of time the code runs for
    max_samples : int
        The total number of samples to take
    fig : matplotlib.pyplot.figure
        Overall figure for all of the subplots
    roll_plot : AniPlot object
        Plots the roll of one or both pucks
    pitch_plot : AniPlot object
        Plots the pitch of one or both pucks
    yaw_plot : AniPlot object
        Plots the yaw of one or both pucks
    x_gyro_plot : AniPlot object
        Plots the x coordinate of the gyroscope of one or both pucks
    y_gyro_plot : AniPlot object
        Plots the y coordinate of the gyroscope of one or both pucks      
    z_gyro_plot : AniPlot object
        Plots the x coordinate of the gyroscope of one or both pucks
    x_acceleration_plot : AniPlot object
        Plots the x rotational acceleration of the accelerometer of one or both
        pucks
    y_acceleration_plot : AniPlot object
        Plots the y rotational acceleration of the accelerometer of one or both
        pucks
    z_acceleration_plot : AniPlot object
        Plots the z rotational acceleration of the accelerometer of one or both
        pucks
    x_velocity_plot : AniPlot object
        Plots the x linear velocity of one or both pucks
    y_velocity_plot : AniPlot object
        Plots the y linear velocity of one or both pucks
    z_velocity_plot : AniPlot object
        Plots the z linear velocity of one or both pucks
    load_cell_plot : AniPlot object
        Plots the force on the load cell of one or both pucks
    puck : HIDPuckDongle object
        Connects to the dongle for communicating to and from the pucks

    Methods
    -------
    __init__()
        Creates subplots to show data from the FitMi pucks
    start()
        Starts recording from the pucks and polls based on sample rate
    stop()
        Stops recording from the pucks and close the dongle connection
    run(puck_0_data, puck_1_data)
        Updates each data plot based on the polled data
    update_buffers(puck_0_data, puck_1_data)
        Uses polled data to update AniPlot subplots
    '''
    def __init__(self):
        '''
        Creates subplots to show data from the FitMi pucks

        Formats the figure the data is plotted on. Allows the user to tweak
        plotting ranges and labels.     
        '''
        self.samples_per_second = 60
        self.max_run_time_seconds = 100
        self.max_samples = self.samples_per_second * self.max_run_time_seconds

        buffer_min = 0 # minimum of x axis on plots
        buffer_max = 200 # maximum of x axis of plots

        # y axis range for the roll, pitch yaw plots
        angle_ymax = 180
        angle_ymin = -angle_ymax

        # y axis range of the gyroscope plots
        gyro_ymax = 1100
        gyro_ymin = -gyro_ymax

        # y axis range of the accelerometer plots
        acceleration_ymax = 1000
        acceleration_ymin = -acceleration_ymax

        # y axis range of the linear velocity plots
        velocity_ymax = 500
        velocity_ymin = -velocity_ymax

        # y axis range of the load cell plot
        load_cell_ymax = 1100
        load_cell_ymin = 0

        # create a figure and set its size and the size of the subplots so the
        # labels don't overlap
        self.fig = plt.figure()
        self.fig.suptitle("FitMi Puck Data", fontsize = 20)
        self.fig.set_size_inches(20, 10, forward = True)
        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9,
            wspace=0.4, hspace=0.4)

        # create and label the angular rotation plots
        self.roll_plot = AniPlot(self.fig, [5, 3, 1], buffer_min, buffer_max,
            angle_ymin / 2, angle_ymax / 2, second_puck=True)
        self.roll_plot.set_ylabel("roll angle")
        self.pitch_plot = AniPlot(self.fig, [5, 3, 2], buffer_min, buffer_max,
            angle_ymin, angle_ymax, second_puck=True)
        self.pitch_plot.set_ylabel("pitch angle")
        self.yaw_plot = AniPlot(self.fig, [5, 3, 3], buffer_min, buffer_max,
            angle_ymin, angle_ymax, second_puck=True)
        self.yaw_plot.set_ylabel("yaw angle")

        # create and label the gyroscope plots
        self.x_gyro_plot = AniPlot(self.fig, [5, 3, 4], buffer_min, buffer_max,
            gyro_ymin, gyro_ymax, second_puck=True)
        self.x_gyro_plot.set_ylabel("x gyroscope")
        self.y_gyro_plot = AniPlot(self.fig, [5, 3, 5], buffer_min, buffer_max,
            gyro_ymin, gyro_ymax, second_puck=True)
        self.y_gyro_plot.set_ylabel("y gyroscope")
        self.z_gyro_plot = AniPlot(self.fig, [5, 3, 6], buffer_min, buffer_max,
            gyro_ymin, gyro_ymax, second_puck=True)
        self.z_gyro_plot.set_ylabel("z gyroscope")

        # create and label the accelerometer plots. NOTE: These are angular
        # accelerations
        self.x_acceleration_plot = AniPlot(self.fig, [5, 3, 7], buffer_min,
             buffer_max, acceleration_ymin, acceleration_ymax, second_puck=True)
        self.x_acceleration_plot.set_ylabel("x rotational acceleration")
        self.y_acceleration_plot = AniPlot(self.fig, [5, 3, 8], buffer_min,
            buffer_max, acceleration_ymin, acceleration_ymax, second_puck=True)
        self.y_acceleration_plot.set_ylabel("y rotational acceleration")
        self.z_acceleration_plot = AniPlot(self.fig, [5, 3, 9], buffer_min,
            buffer_max, acceleration_ymin, acceleration_ymax, second_puck=True)
        self.z_acceleration_plot.set_ylabel("z rotational acceleration")

        # create and label the velocity plots
        self.x_velocity_plot = AniPlot(self.fig, [5, 3, 10], buffer_min,
            buffer_max, velocity_ymin, velocity_ymax, second_puck=True)
        self.x_velocity_plot.set_ylabel("x velocity")
        self.y_velocity_plot = AniPlot(self.fig, [5, 3, 11], buffer_min,
            buffer_max, velocity_ymin, velocity_ymax, second_puck=True)
        self.y_velocity_plot.set_ylabel("y velocity")
        self.z_velocity_plot = AniPlot(self.fig, [5, 3, 12], buffer_min,
            buffer_max, velocity_ymin, velocity_ymax, second_puck=True)
        self.z_velocity_plot.set_ylabel("z velocity")

        # create and label the load cell plot
        self.load_cell_plot = AniPlot(self.fig, [5, 1, 5], buffer_min,
            buffer_max, ymin=load_cell_ymin, ymax=load_cell_ymax,
            second_puck=True)
        self.load_cell_plot.set_ylabel("load cell")

        # aligns all of the created y axis labels and refresh the plot
        self.fig.align_ylabels(self.fig.axes)
        self.fig.canvas.draw()

        # Connect to the dongle for puck communication
        self.puck = HIDPuckDongle()

    def start(self):
        '''
        Starts recording from the pucks and polls based on sample rate
        '''
        # Send command to communicate with both pucks
        self.puck.open()
        self.puck.send_command(0, SENDVEL, 0x00, 0x01)
        self.puck.send_command(1, SENDVEL, 0x00, 0x01)

        # sample both pucks and pause by the sample rate
        for i in range(self.max_samples):
            self.puck.checkForNewPuckData()
            # send queried data to the plots and update them
            self.run(self.puck.puck_0_packet, self.puck.puck_1_packet)
            time.sleep(1.0/self.samples_per_second)

    def stop(self):
        '''
        Stops recording from the pucks and close the dongle connection
        '''
        self.puck.send_command(0, SENDVEL, 0x00, 0x00)
        self.puck.send_command(1, SENDVEL, 0x00, 0x00)
        self.puck.close()

    def run(self, puck_0_data=None, puck_1_data=None):
        '''
        Updates each data plot based on the polled data

        Sends the polled data to each of the AniPlot objects to update them and
        then redraws the plots. This also checks if you are touching the pucks
        to change the color of the load cell plots.

        Parameters
        ----------
        puck_0_data : PuckPacket object, optional
            Contains all of the polled data from puck 0, the blue one
        puck_1_data : PuckPacket object, optional
            Contains all of the polled data from puck 1, the yellow one
        '''
        self.update_buffers(puck_0_data, puck_1_data)

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

        if puck_0_data.touch:
            self.load_cell_plot.puck_1_plot.set_color("r")
        else:
            self.load_cell_plot.puck_1_plot.set_color("b")

        if puck_1_data.touch and self.load_cell_plot.puck_2_plot:
            self.load_cell_plot.puck_2_plot.set_color("m")
        else:
            self.load_cell_plot.puck_2_plot.set_color("g")

    def update_buffers(self, puck_0_data, puck_1_data):
        '''
        Uses polled data to update AniPlot subplots

        Takes an input of data from the pucks and parses the data to update
        individual plots. This method also buzzes the puck if the user moves it
        fast.

        Parameters
        ----------
        puck_0_data : PuckPacket object
            Contains all of the polled data from puck 0, the blue one
        puck_1_data : PuckPacket object
            Contains all of the polled data from puck 1, the yellow one
        '''
        self.roll_plot.update(puck_0_data.roll_pitch_yaw[0],
            puck_1_data.roll_pitch_yaw[0])
        self.pitch_plot.update(puck_0_data.roll_pitch_yaw[1],
            puck_1_data.roll_pitch_yaw[1])
        self.yaw_plot.update(puck_0_data.roll_pitch_yaw[2],
            puck_1_data.roll_pitch_yaw[2])

        self.x_gyro_plot.update(puck_0_data.gyroscope[0],
            puck_1_data.gyroscope[0])
        self.y_gyro_plot.update(puck_0_data.gyroscope[1],
            puck_1_data.gyroscope[1])
        self.z_gyro_plot.update(puck_0_data.gyroscope[2],
            puck_1_data.gyroscope[2])

        self.x_acceleration_plot.update(puck_0_data.accelerometer[0],
            puck_1_data.accelerometer[0])
        self.y_acceleration_plot.update(puck_0_data.accelerometer[1],
            puck_1_data.accelerometer[1])
        self.z_acceleration_plot.update(puck_0_data.accelerometer[2],
            puck_1_data.accelerometer[2])

        self.x_velocity_plot.update(puck_0_data.velocity[0],
            puck_1_data.velocity[0])
        self.y_velocity_plot.update(puck_0_data.velocity[1],
            puck_1_data.velocity[1])
        self.z_velocity_plot.update(puck_0_data.velocity[2],
            puck_1_data.velocity[2])
        
        self.load_cell_plot.update(puck_0_data.load_cell, puck_1_data.load_cell)

if __name__ == '__main__':
    '''
    Creates the puck plotter and starts it.
    '''
    plotter = PuckPlotter()
    try:
        plotter.start()
    finally:
        plotter.stop()
