##----------------------------------------------------------------------------##
##---- show the orientation of our device ------------------------------------##
##----------------------------------------------------------------------------##
## the accuracy of our velocity estimates is limmited by the accuracy of our
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
    def __init__(self, pucknum=0):
        self.puck = HIDPuckDongle()
        self.fs = 40
        self.n_seconds = 100
        self.max_samples = self.fs*self.n_seconds
        self.pucknum = pucknum

        self.fig = plt.figure()
        self.fig.set_size_inches(6, 6, forward=True)
        self.ax = self.fig.add_subplot(111, projection='3d') #projection='3d'
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)
        self.ax.set_zlim(-2, 2)

        self.fig.show(False)
        plt.draw()
        self.bg = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        linex = [0, 1, 0, 0]
        liney = [0, 0, 1, 0]
        linez = [0, 0, 0, 1]
        self.datplot = self.ax.scatter(linex, liney, linez, c="b")

    def start_scope(self):
        self.puck.open()
        self.puck.sendCommand(self.pucknum,SENDVEL, 0x00, 0x01)

        tickup = 0
        print "recording data"
        for i in range(0, self.max_samples):
            self.puck.checkForNewPuckData()
            self.update_plot()


            time.sleep(1.0/self.fs)
            tickup+=1
            if tickup > self.fs:
                tickup=0
                print".",

        self.puck.stop()


    def update_plot(self):
        if self.pucknum == 1:
            pdata = self.puck.puck_packet_1
        else:
            pdata = self.puck.puck_packet_0

        vx = np.array([1,0,0])
        vx = q_vector_multiply(pdata.quaternion, vx)

        vy = np.array([0,1,0])
        vy = q_vector_multiply(pdata.quaternion, vy)

        vz = np.array([0,0,1])
        vz = q_vector_multiply(pdata.quaternion, vz)

        linex = [0, vx[0], vy[0], vz[0]]
        liney = [0, vx[1], vy[1], vz[1]]
        linez = [0, vx[2], vy[2], vz[2]]

        if self.datplot:
            self.ax.collections.remove(self.datplot)
        self.datplot = self.ax.scatter(linex, liney, linez, c="b")
        plt.pause(.00005)

        # self.datplot._offsets3d = juggle_axes(linex, liney, linez, 'z')

if __name__ == "__main__":
    oscope = OrientationScope()
    try:
        oscope.start_scope()
    finally:
        oscope.puck.stop()
