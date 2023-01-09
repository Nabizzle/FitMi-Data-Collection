from matplotlib import pyplot as plt
from typing import List
from Puck.puck_packet import PuckPacket


class AniPlot(object):
    '''
    Creates a subplot to display a buffer to data

    Sets up the subplot for one or both pucks and updates the plots upon
    function call. NOTE: AniPlot stands for animated plot

    Attributes
    ----------
    fig : matplotlib.pyplot.figure
        Overall data figure
    ax : matplotlib.pyplot.axis
        Axis of the subplot
    bg : plot region
        Copy of the subplot region
    puck_0_data : List[int]
        List of 0's the length of the buffer for the blue puck's data
    puck_1_data : List[int]
        List of 0's the length of the buffer for the yellow puck's data

    Methods
    -------
    __init__(fig, split, buffer_min, buffer_max, ymin, ymax, second_puck)
        Create the base data subplot
    set_xlabel
        Sets the x axis label of the subplot
    set_ylabel
        Sets the y axis label of the subplot
    update(puck_0_data, puck_1_data):
        Add the new data to the end of the buffer of data
    draw(fig):
        Adds the data to the subplot
    '''
    def __init__(self, fig: plt.figure, split: List[int], buffer_min: int = 0,
                 buffer_max: int = 200, ymin: int = -180, ymax: int = 180,
                 second_puck: bool = False):
        '''
        Create the base data subplot

        Create the subplot for the data with a buffer of base line values
        before the data gets updated.

        Parameters
        ----------
        fig : matplotlib.pyplot.figure
            Figure for all of the data plots
        split : List[int]
            Values for the row, column, and plot number
        buffer_min : int, default = 0
            start of the buffer (should be 0)
        buffer_max : int, default = 200
            end point of the buffer
        ymin : int, default = -180
            bottom of the y axis
        ymax : int, default = 180
            top of the y axis
        second_puck : bool, default = False
            Indicates if you want to plot the second puck's data (True = yes)
        '''
        self.fig = fig  # moves the data figure a class attribute
        # create the subplot based on input parameters for the plot number and
        # the axis limits
        self.ax = fig.add_subplot(split[0], split[1], split[2],
                                  xlim=(buffer_min, buffer_max),
                                  ylim=(ymin, ymax))

        # display the figure and update it
        fig.show(False)
        fig.canvas.draw()

        # copy the subplot region
        self.bg = self.fig.canvas.copy_from_bbox(self.ax.bbox)

        # create the base line for the blue puck and set the puck puck's line
        # to None
        self.puck_0_data = [0]*(buffer_max - buffer_min)
        self.puck_1_data = None

        # If you want to plot the second puck's data, create the base line for
        # the yellow puck
        if second_puck:
            self.puck_1_data = [0]*(buffer_max - buffer_min)

        # create the x values for the data plot
        self.x_points = range(buffer_min, buffer_max)

        # plot the base line of the blue puck in blue
        self.puck_1_plot = self.ax.plot(self.x_points, self.puck_0_data, '-',
                                        color="b")[0]
        self.puck_2_plot = None

        # if there is a need to plot a second puck, plot the yellow puck in
        # green
        if second_puck:
            self.puck_2_plot = self.ax.plot(self.x_points, self.puck_1_data,
                                            '-', color="g")[0]

    def set_xlabel(self, axis_name: str):
        '''
        Sets the x axis label of the subplot

        Parameters
        ----------
        axis_name : string
            The label for the x axis
        '''
        # set the x axis label with a font size of 12 and redraw the figure
        self.ax.set_xlabel(axis_name, fontsize=12)
        self.fig.canvas.draw()

    def set_ylabel(self, axis_name: str):
        '''
        Sets the y axis label of the subplot

        Parameters
        ----------
        axis_name : string
            The label for the y axis
        '''
        # set the y axis label with a font size of 12 and redraw the figure
        self.ax.set_ylabel(axis_name, fontsize=12)
        self.fig.canvas.draw()

    def update(self, puck_0_data: PuckPacket, puck_1_data: PuckPacket = None):
        '''
        Add the new data to the end of the buffer of data

        Adds new data to the end of the data buffer and removes the first point
        in the buffer.

        Parameters
        ----------
        puck_0_data : int
            new data from the blue puck
        puck_1_data : int
            new data from the yellow puck
        '''
        # adds data to the end of the blue puck buffer and removes the first
        # point
        self.puck_0_data.pop(0)
        self.puck_0_data.append(puck_0_data)

        # if you want to track two pucks, adds data to the end of the yellow
        # puck buffer and removes the first point
        if (puck_1_data is not None) and (self.puck_1_data is not None):
            self.puck_1_data.pop(0)
            self.puck_1_data.append(puck_1_data)

    def draw(self, fig: plt.figure):
        '''
        Adds the data to the subplot

        Adds the data from the data buffers to the plot and redraws it for the
        animation.

        Parameters
        ----------
        fig : matplotlib.pyplot.figure
            Figure for all of the data plots
        '''
        # adds data from the pucks to the plot
        self.puck_1_plot.set_data(self.x_points, self.puck_0_data)
        if self.puck_2_plot and self.puck_1_data:
            self.puck_2_plot.set_data(self.x_points, self.puck_1_data)

        # redraw the figure
        fig.canvas.restore_region(self.bg)
        self.ax.draw_artist(self.puck_1_plot)
        if self.puck_2_plot:
            self.ax.draw_artist(self.puck_2_plot)

        fig.canvas.blit(self.ax.bbox)
