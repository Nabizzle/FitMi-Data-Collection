##----------------------------------------------------------------------------##
##---- show the orientation of our device ------------------------------------##
##----------------------------------------------------------------------------##
## the accuracy of our velocity estimates is limited by the accuracy of our
## orientation estimates. Even a small amount of error builds up over time.
## we need to improve our orientation estimates. To do that I need a better tool
## for visualizing our error.

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import juggle_axes
import matplotlib

from Puck.Quaternion import *

from Puck import HIDPuckDongle
from Puck.hid_puck import *

matplotlib.interactive(True)

class OrientationScope(object):
    def __init__(self, puck_number = 1):
        self.puck = HIDPuckDongle()
        self.fs = 40
        self.n_seconds = 100
        self.max_samples = self.fs*self.n_seconds
        self.puck_number = puck_number

        self.fig = plt.figure()
        self.fig.set_size_inches(6, 6, forward=True)
        self.ax = self.fig.add_subplot(111, projection='3d') #projection='3d'
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)
        self.ax.set_zlim(-2, 2)

        self.fig.show(False)
        plt.draw()
        self.bg = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        line_x = [0, 1, 0, 0]
        line_y = [0, 0, 1, 0]
        line_z = [0, 0, 0, 1]
        self.data_plot = self.ax.scatter(line_x, line_y, line_z, c="b")

    def start_scope(self):
        self.puck.open()
        self.puck.sendCommand(self.puck_number,SENDVEL, 0x00, 0x01)

        tick_up = 0
        print("recording data")
        for i in range(0, self.max_samples):
            self.puck.checkForNewPuckData()
            self.update_plot()


            time.sleep(1.0/self.fs)
            tick_up+=1
            if tick_up > self.fs:
                tick_up=0
                print(".")

        self.puck.stop()


    def update_plot(self):
        if self.puck_number == 1:
            puck_data = self.puck.puck_packet_1
        else:
            puck_data = self.puck.puck_packet_0

        vx = np.array([1,0,0])
        vx = q_vector_multiply(puck_data.quaternion, vx)

        vy = np.array([0,1,0])
        vy = q_vector_multiply(puck_data.quaternion, vy)

        vz = np.array([0,0,1])
        vz = q_vector_multiply(puck_data.quaternion, vz)

        line_x = [0, vx[0], vy[0], vz[0]]
        line_y = [0, vx[1], vy[1], vz[1]]
        line_z = [0, vx[2], vy[2], vz[2]]

        if self.data_plot:
            self.ax.collections.remove(self.data_plot)
        self.data_plot = self.ax.scatter(line_x, line_y, line_z, c="b")
        plt.pause(.00005)

if __name__ == "__main__":
    orientation_scope = OrientationScope()
    try:
        orientation_scope.start_scope()
    finally:
        orientation_scope.puck.stop()
