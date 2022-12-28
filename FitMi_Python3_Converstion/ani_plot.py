##----------------------------------------------------------------------------##
##---- an animating subplot --------------------------------------------------##
##----------------------------------------------------------------------------##

from matplotlib import pyplot as plt

class AniPlot(object):
    def __init__(self, fig, spilt_number, buffer_min=0, buffer_max=200, ymin=-180, ymax=180, double=False):
        self.ax = fig.add_subplot(spilt_number)
        self.ax.set_xlim(buffer_min, buffer_max)
        self.ax.set_ylim(ymin, ymax)
        self.ax.hold(True)

        fig.show(False)
        plt.draw()

        self.bg = fig.canvas.copy_from_bbox(self.ax.bbox)

        self.buff = [0]*(buffer_max - buffer_min)
        self.buff2 = None
        if double:
            self.buff2 = [0]*(buffer_max - buffer_min)
        self.x_points = range(buffer_min, buffer_max)

        self.plt = self.ax.plot(self.x_points, self.buff, '-', color="b")[0]
        self.plt2 = None
        if double:
            self.plt2 = self.ax.plot(self.x_points, self.buff2, '-', color="g")[0]

    def set_xlabel(self, axis_name):
        self.ax.set_xlabel(axis_name)

    def set_ylabel(self, axis_name):
        self.ax.set_ylabel(axis_name)

    def update(self, data1, data2=None):
        self.buff.pop(0)
        self.buff.append(data1)

        if (not data2 is None) and (not self.buff2 is None):
            self.buff2.pop(0)
            self.buff2.append(data2)

    def draw(self, fig):
        self.plt.set_data(self.x_points, self.buff)
        if self.plt2 and self.buff2:
            self.plt2.set_data(self.x_points, self.buff2)

        fig.canvas.restore_region(self.bg)
        self.ax.draw_artist(self.plt)
        if self.plt2:
            self.ax.draw_artist(self.plt2)

        fig.canvas.blit(self.ax.bbox)
