import matplotlib.pyplot as plt
from Puck.quaternion import *
from Puck.hid_puck import HIDPuckDongle
from Puck.hid_puck import *


class OrientationScope(object):
    '''
    Creates a visualization of the puck in 3D space

    Allows the user to visualize the rotations of one of the two pucks on a 3D
    axis. This is done as a x, y, z gizmo that rotates with the puck.

    Attributes
    ----------
    puck : HIDPuckDongle object
        Connects to the dongle for communicating to and from the pucks
    samples_per_second : int
        The number of times the pucks are queried per second
    max_run_time_seconds : int
        Total amount of time the code runs for
    max_samples : int
        The total number of samples to take
    puck_number : int
        The blue puck (0) or the yellow puck (1)
    fig : matplotlib.pyplot.figure
        The 3D figure for showing the orientation of the puck
    ax : matplotlib.pyplot.axis
        The axis of the 3D figure
    data_point : matplotlib.pyplot.scatter
        Scatter plot showing the x, y, z axis of the puck

    Methods
    -------
    __init__(puck_number)
        Creates the initial 3D plot of the puck axes
    start_scope()
        Starts communication with puck and updates plot with rotation
    update_plot()
        Takes the puck data and updates the 3D plot of orientation
    '''
    def __init__(self, puck_number: int = 0):
        '''
        Creates the initial 3D plot of the puck axes

        Parameters
        ----------
        puck_number : int, default = 1
            id of the puck. 0 = blue puck, 1 = yellow puck
        '''
        self.puck = HIDPuckDongle()
        self.samples_per_second = 40
        self.max_run_time_seconds = 100
        self.max_samples = self.samples_per_second*self.max_run_time_seconds
        self.puck_number = puck_number

        self.fig = plt.figure()
        self.fig.set_size_inches(6, 6, forward=True)
        self.ax = self.fig.add_subplot(111, projection='3d') #projection='3d'
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)
        self.ax.set_zlim(-2, 2)

        self.fig.show(False)
        plt.draw()
        line_x = [0, 1, 0, 0]
        line_y = [0, 0, 1, 0]
        line_z = [0, 0, 0, 1]
        self.data_plot = self.ax.scatter(line_x, line_y, line_z, c="b")


    def start_scope(self):
        '''
        Starts communication with puck and updates plot with rotation

        Records for the number of samples to reach the max test time with the
        sample rate of the scope. Communication is cut off at the end of the
        sampling.
        '''
        # Creates the connection to the selected puck
        self.puck.open()
        self.puck.send_command(self.puck_number, SENDVEL, 0x00, 0x01)

        tick_up = 0 # counter to indicate when a second has passed
        print("recording data")
        # records data at a time period based on the samples per second
        for i in range(self.max_samples):
            self.puck.checkForNewPuckData()
            self.update_plot() # updates the plots based on the puck data

            time.sleep(1.0/self.samples_per_second)
            tick_up+=1
            # plot a dot when a second has passed
            if tick_up > self.samples_per_second:
                tick_up=0
                print(".")

        self.puck.stop()



    def update_plot(self):
        '''
        Takes the puck data and updates the 3D plot of orientation

        Selects which puck data packet to use and updates orientation based on
        the puck's quaternion
        '''
        # selects the puck data packet based on the puck's id
        if self.puck_number == 1:
            puck_data = self.puck.puck_1_packet
        else:
            puck_data = self.puck.puck_0_packet

        # make a vector of each axis and rotate it by the puck's quaternion
        vx = np.array([1,0,0])
        vx = q_rotate_vector(puck_data.quaternion, vx)

        vy = np.array([0,1,0])
        vy = q_rotate_vector(puck_data.quaternion, vy)

        vz = np.array([0,0,1])
        vz = q_rotate_vector(puck_data.quaternion, vz)

        # draw a line to each rotated axis
        line_x = [0, vx[0], vy[0], vz[0]]
        line_y = [0, vx[1], vy[1], vz[1]]
        line_z = [0, vx[2], vy[2], vz[2]]

        # redraw the scatter plot of the puck's orientation
        if self.data_plot:
            self.ax.collections.remove(self.data_plot)
        self.data_plot = self.ax.scatter(line_x, line_y, line_z, c="b")
        plt.pause(.00005) # pause infinitesimal amount of time to allow update.


if __name__ == "__main__":
    '''
    start the scope to watch the puck orientation
    '''
    orientation_scope = OrientationScope()
    try:
        orientation_scope.start_scope()
    finally:
        orientation_scope.puck.stop()
