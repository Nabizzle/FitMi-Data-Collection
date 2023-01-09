import customtkinter as ctk
import seaborn as sns
from matplotlib.style import context
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from Puck.puck_packet import PuckPacket
from Puck.hid_puck import HIDPuckDongle
from Puck.hid_puck import SENDVEL


# Modes: "System" (standard), "Dark", "Light"
ctk.set_appearance_mode("System")
# Themes: "blue" (standard), "green", "dark-blue"
ctk.set_default_color_theme("dark-blue")


class PlottingApp(ctk.CTk):
    SAMPLES_PER_SECOND = 60
    MAX_RUN_TIME_SECONDS = 100
    MAX_SAMPLES = SAMPLES_PER_SECOND * MAX_RUN_TIME_SECONDS

    PAD_X = 5
    PAD_Y = 5

    PLOT_X = 500
    PLOT_Y = 150

    BUFFER_MIN = 0 # minimum of x axis on plots
    BUFFER_MAX = 200 # maximum of x axis of plots

    # y axis range for the roll, pitch yaw plots
    ANGLE_YMAX = 180
    ANGLE_YMIN = -ANGLE_YMAX

    # y axis range of the gyroscope plots
    GYRO_YMAX = 1100
    GYRO_YMIN = -GYRO_YMAX

    # y axis range of the accelerometer plots
    ACCELERATION_YMAX = 1000
    ACCELERATION_YMIN = -ACCELERATION_YMAX

    # y axis range of the linear velocity plots
    VELOCITY_YMAX = 500
    VELOCITY_YMIN = -VELOCITY_YMAX

    # y axis range of the load cell plot
    LOAD_CELL_YMAX = 1100
    LOAD_CELL_YMIN = 0

    def __init__(self):
        super().__init__()
        self.title("Puck Data Output")
        self.geometry(f"{self.PLOT_X * 3 + 6 * self.PAD_X}x"
                      f"{self.PLOT_Y * 5 + 100 + 10 * self.PAD_Y}")
        self.grid_columnconfigure((0, 1, 2), weight=0)
        self.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=0)
        self.keep_running = False

        self.roll_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                     fig_y=self.PLOT_Y / 100,
                                     buffer_min=self.BUFFER_MIN,
                                     buffer_max=self.BUFFER_MAX,
                                     y_min=self.ANGLE_YMIN / 2,
                                     y_max=self.ANGLE_YMAX / 2)
        self.roll_plot.grid(row = 0, column = 0, padx = self.PAD_X,
                            pady = self.PAD_Y)
        self.roll_plot.set_title("roll angle")

        self.pitch_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                      fig_y=self.PLOT_Y / 100,
                                      buffer_min=self.BUFFER_MIN,
                                      buffer_max=self.BUFFER_MAX,
                                      y_min=self.ANGLE_YMIN,
                                      y_max=self.ANGLE_YMAX)
        self.pitch_plot.grid(row = 0, column = 1, padx = self.PAD_X,
                             pady = self.PAD_Y)
        self.pitch_plot.set_title("pitch angle")

        self.yaw_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                    fig_y=self.PLOT_Y / 100,
                                    buffer_min=self.BUFFER_MIN,
                                    buffer_max=self.BUFFER_MAX,
                                    y_min=self.ANGLE_YMIN,
                                    y_max=self.ANGLE_YMAX)
        self.yaw_plot.grid(row = 0, column = 2, padx = self.PAD_X,
                           pady = self.PAD_Y)
        self.yaw_plot.set_title("yaw angle")

        self.x_gyro_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                       fig_y=self.PLOT_Y / 100,
                                       buffer_min=self.BUFFER_MIN,
                                       buffer_max=self.BUFFER_MAX,
                                       y_min=self.GYRO_YMIN,
                                       y_max=self.GYRO_YMAX)
        self.x_gyro_plot.grid(row = 1, column = 0, padx = self.PAD_X,
                              pady = self.PAD_Y)
        self.x_gyro_plot.set_title("x gyroscope")

        self.y_gyro_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                       fig_y=self.PLOT_Y / 100,
                                       buffer_min=self.BUFFER_MIN,
                                       buffer_max=self.BUFFER_MAX,
                                       y_min=self.GYRO_YMIN,
                                       y_max=self.GYRO_YMAX)
        self.y_gyro_plot.grid(row = 1, column = 1, padx = self.PAD_X,
                              pady = self.PAD_Y)
        self.y_gyro_plot.set_title("y gyroscope")

        self.z_gyro_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                       fig_y=self.PLOT_Y / 100,
                                       buffer_min=self.BUFFER_MIN,
                                       buffer_max=self.BUFFER_MAX,
                                       y_min=self.GYRO_YMIN,
                                       y_max=self.GYRO_YMAX)
        self.z_gyro_plot.grid(row = 1, column = 2, padx = self.PAD_X,
                              pady = self.PAD_Y)
        self.z_gyro_plot.set_title("z gyroscope")

        self.x_acceleration_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                               fig_y=self.PLOT_Y / 100,
                                               buffer_min=self.BUFFER_MIN,
                                               buffer_max=self.BUFFER_MAX,
                                               y_min=self.ACCELERATION_YMIN,
                                               y_max=self.ACCELERATION_YMAX)
        self.x_acceleration_plot.grid(row = 2, column = 0, padx = self.PAD_X,
                                      pady = self.PAD_Y)
        self.x_acceleration_plot.set_title("x acceleration")

        self.y_acceleration_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                               fig_y=self.PLOT_Y / 100,
                                               buffer_min=self.BUFFER_MIN,
                                               buffer_max=self.BUFFER_MAX,
                                               y_min=self.ACCELERATION_YMIN,
                                               y_max=self.ACCELERATION_YMAX)
        self.y_acceleration_plot.grid(row = 2, column = 1, padx = self.PAD_X,
                                      pady = self.PAD_Y)
        self.y_acceleration_plot.set_title("y acceleration")

        self.z_acceleration_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                               fig_y=self.PLOT_Y / 100,
                                               buffer_min=self.BUFFER_MIN,
                                               buffer_max=self.BUFFER_MAX,
                                               y_min=self.ACCELERATION_YMIN,
                                               y_max=self.ACCELERATION_YMAX)
        self.z_acceleration_plot.grid(row = 2, column = 2, padx = self.PAD_X,
                                      pady = self.PAD_Y)
        self.z_acceleration_plot.set_title("z acceleration")

        self.x_velocity_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                           fig_y=self.PLOT_Y / 100,
                                           buffer_min=self.BUFFER_MIN,
                                           buffer_max=self.BUFFER_MAX,
                                           y_min=self.VELOCITY_YMIN,
                                           y_max=self.VELOCITY_YMAX)
        self.x_velocity_plot.grid(row = 3, column = 0, padx = self.PAD_X,
                                  pady = self.PAD_Y)
        self.x_velocity_plot.set_title("x velocity")

        self.y_velocity_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                           fig_y=self.PLOT_Y / 100,
                                           buffer_min=self.BUFFER_MIN,
                                           buffer_max=self.BUFFER_MAX,
                                           y_min=self.VELOCITY_YMIN,
                                           y_max=self.VELOCITY_YMAX)
        self.y_velocity_plot.grid(row = 3, column = 1, padx = self.PAD_X,
                                  pady = self.PAD_Y)
        self.y_velocity_plot.set_title("y velocity")

        self.z_velocity_plot = DataSubplot(self, fig_x=self.PLOT_X / 100,
                                           fig_y=self.PLOT_Y / 100,
                                           buffer_min=self.BUFFER_MIN,
                                           buffer_max=self.BUFFER_MAX,
                                           y_min=self.VELOCITY_YMIN,
                                           y_max=self.VELOCITY_YMAX)
        self.z_velocity_plot.grid(row = 3, column = 2, padx = self.PAD_X,
                                  pady = self.PAD_Y)
        self.z_velocity_plot.set_title("z velocity")

        self.load_cell_plot = DataSubplot(self, fig_x=self.PLOT_X * 3 / 100,
                                          fig_y=self.PLOT_Y / 100,
                                          buffer_min=self.BUFFER_MIN,
                                          buffer_max=self.BUFFER_MAX,
                                          y_min=self.LOAD_CELL_YMIN,
                                          y_max=self.LOAD_CELL_YMAX)
        self.load_cell_plot.grid(row = 4, column = 0, columnspan = 3)
        self.load_cell_plot.set_title("load cell")

        # Create the start recording button
        self.start_button = ctk.CTkButton(self, text = "Start Recording",
                                          command = self.start_button_callback,
                                          width=500, height=100,
                                          font=("Ariel", 24))
        self.start_button.grid(row = 5, column = 0, padx = self.PAD_X,
                               pady = self.PAD_Y)

        # Create the stop recording button
        self.stop_button = ctk.CTkButton(self, text = "Stop Recording",
                                         command = self.stop_button_callback,
                                         width=500, height=100,
                                         font=("Ariel", 24))
        self.stop_button.grid(row = 5, column = 1, padx = self.PAD_X,
                              pady = self.PAD_Y)

        # Create scrollbar for buffer size
        self.buffer_slider = ctk.CTkSlider(self, orientation="horizontal",
                                           width=500, from_=20, to=500,
                                           command=self.slider_callback)
        self.buffer_slider.grid(row = 5, column = 2, padx = self.PAD_X,
                                pady = self.PAD_Y)
        self.buffer_slider.set(200)

        # Connect to the dongle for puck communication
        self.puck = HIDPuckDongle()

        self.after(int(1000/self.SAMPLES_PER_SECOND), self.get_data)

    def start_button_callback(self):
        '''
        Starts recording from the pucks and polls based on sample rate
        '''
        self.samples_taken = 0
        # Send command to communicate with both pucks
        self.puck.open()
        self.puck.send_command(0, SENDVEL, 0x00, 0x01)
        self.puck.send_command(1, SENDVEL, 0x00, 0x01)

        # sample both pucks and pause by the sample rate
        self.keep_running = True

    def stop_button_callback(self):
        '''
        Tells the app to stop recording and disconnects for the pucks
        '''
        print("Recording Stopped")
        self.keep_running = False
        self.puck.send_command(0, SENDVEL, 0x00, 0x00)
        self.puck.send_command(1, SENDVEL, 0x00, 0x00)
        self.puck.close()

    def slider_callback(self, slider_value):
        slider_value = int(slider_value)
        self.roll_plot.set_xlim(slider_value)
        self.pitch_plot.set_xlim(slider_value)
        self.yaw_plot.set_xlim(slider_value)

        self.x_gyro_plot.set_xlim(slider_value)
        self.y_gyro_plot.set_xlim(slider_value)
        self.z_gyro_plot.set_xlim(slider_value)

        self.x_acceleration_plot.set_xlim(slider_value)
        self.y_acceleration_plot.set_xlim(slider_value)
        self.z_acceleration_plot.set_xlim(slider_value)

        self.x_velocity_plot.set_xlim(slider_value)
        self.y_velocity_plot.set_xlim(slider_value)
        self.z_velocity_plot.set_xlim(slider_value)

        self.load_cell_plot.set_xlim(slider_value)

    def get_data(self):
        '''
        Record the data on each sample time step
        '''
        if self.keep_running and (self.samples_taken < self.MAX_SAMPLES):
            self.puck.checkForNewPuckData()
            # send queried data to the plots and update them
            self.samples_taken += 1
            self.run(self.puck.puck_0_packet, self.puck.puck_1_packet)

        self.after(int(1000/self.SAMPLES_PER_SECOND), self.get_data)

    def run(self, puck_0_data: PuckPacket = None,
        puck_1_data: PuckPacket = None):
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

        self.roll_plot.draw()
        self.pitch_plot.draw()
        self.yaw_plot.draw()

        self.x_gyro_plot.draw()
        self.y_gyro_plot.draw()
        self.z_gyro_plot.draw()

        self.x_acceleration_plot.draw()
        self.y_acceleration_plot.draw()
        self.z_acceleration_plot.draw()

        self.x_velocity_plot.draw()
        self.y_velocity_plot.draw()
        self.z_velocity_plot.draw()

        self.load_cell_plot.draw()

        if puck_0_data.touch:
            self.load_cell_plot.puck_1_plot.set_color("r")
        else:
            self.load_cell_plot.puck_1_plot.set_color("b")

        if puck_1_data.touch and self.load_cell_plot.puck_2_plot:
            self.load_cell_plot.puck_2_plot.set_color("m")
        else:
            self.load_cell_plot.puck_2_plot.set_color("g")

    def update_buffers(self, puck_0_data: PuckPacket, puck_1_data: PuckPacket):
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


class DataSubplot(ctk.CTkFrame):
    def __init__(self, *args, fig_x: float = 5.0, fig_y: float = 2.0,
                 buffer_min: int = 0, buffer_max: int = 200, y_min: int,
                 y_max: int, second_puck: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        sns.set_theme(context='poster', font_scale=0.5)
        plt.style.use('dark_background')
        self.fig = Figure(figsize=(fig_x, fig_y))
        self.data_plot = self.fig.add_subplot(111)
        self.data_plot.set_xlim(buffer_min, buffer_max)
        self.data_plot.set_ylim(y_min, y_max)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)  
        self.canvas.get_tk_widget().pack()
        self.canvas.draw()

        # copy the subplot region
        self.bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)

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
        self.puck_1_plot = self.data_plot.plot(self.x_points,
                                               self.puck_0_data, '-',
                                               color="b")[0]
        self.puck_2_plot = None

        # if there is a need to plot a second puck, plot the yellow puck in
        # green
        if second_puck:
            self.puck_2_plot = self.data_plot.plot(self.x_points,
                                                   self.puck_1_data,
                                                   '-', color="g")[0]

    def set_title(self, axis_name: str):
        self.data_plot.set_title(axis_name)
        self.canvas.draw()

    def set_xlim(self, upper: int):
        self.data_plot.set_xlim(0, upper)
        self.puck_0_data = [0]*(upper)
        self.puck_1_data = [0]*(upper)
        self.x_points = range(upper)
        self.draw()
        self.canvas.draw()

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
        if (not puck_1_data is None) and (not self.puck_1_data is None):
            self.puck_1_data.pop(0)
            self.puck_1_data.append(puck_1_data)

    def draw(self):
        '''
        Adds the data to the subplot

        Adds the data from the data buffers to the plot and redraws it for the
        animation.
        '''
        # adds data from the pucks to the plot
        self.puck_1_plot.set_data(self.x_points, self.puck_0_data)
        if self.puck_2_plot and self.puck_1_data:
            self.puck_2_plot.set_data(self.x_points, self.puck_1_data)

        # redraw the figure
        self.fig.canvas.restore_region(self.bg)
        self.data_plot.draw_artist(self.puck_1_plot)
        if self.puck_2_plot:
            self.data_plot.draw_artist(self.puck_2_plot)

        self.fig.canvas.blit(self.data_plot.bbox)


if __name__ == "__main__":
    app = PlottingApp()
    try:
        app.mainloop()
    finally:
        app.stop_button_callback()
