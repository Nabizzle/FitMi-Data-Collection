##----------------------------------------------------------------------------##
##---- an animating subplot --------------------------------------------------##
##----------------------------------------------------------------------------##

from matplotlib import pyplot as plt

class AniPlot(object):
    def __init__(self, fig, ax, buffer_min=0, buffer_max=200, ymin=-180, ymax=180, second_puck=False):
        self.ax = ax
        self.ax.set_xlim(buffer_min, buffer_max)

        fig.show(False)
        plt.draw()

        
        self.bg = fig.canvas.copy_from_bbox(self.ax.bbox)

        self.zero_line = [0]*(buffer_max - buffer_min)
        self.zero_line_2 = None
        if second_puck:
            self.zero_line_2 = [0]*(buffer_max - buffer_min)
        self.x_points = range(buffer_min, buffer_max)

        self.puck_1_plot = self.ax.plot(self.x_points, self.zero_line, '-', color="b")[0]
        self.puck_2_plot = None
        if second_puck:
            self.puck_2_plot = self.ax.plot(self.x_points, self.zero_line_2, '-', color="g")[0]

    def set_xlabel(self, axis_name):
        self.ax.set(xlabel = axis_name)

    def set_ylabel(self, axis_name):
        self.ax.set(ylabel = axis_name)

    def update(self, data1, data2=None):
        self.zero_line.pop(0)
        self.zero_line.append(data1)

        if (not data2 is None) and (not self.zero_line_2 is None):
            self.zero_line_2.pop(0)
            self.zero_line_2.append(data2)

    def draw(self, fig):
        self.puck_1_plot.set_data(self.x_points, self.zero_line)
        if self.puck_2_plot and self.zero_line_2:
            self.puck_2_plot.set_data(self.x_points, self.zero_line_2)

        fig.canvas.restore_region(self.bg)
        self.ax.draw_artist(self.puck_1_plot)
        if self.puck_2_plot:
            self.ax.draw_artist(self.puck_2_plot)

        fig.canvas.blit(self.ax.bbox)
