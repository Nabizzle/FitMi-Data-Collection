import customtkinter as ctk
import tkinter as tk
from log_puck_data import PuckLogger
from Puck.hid_puck import SENDVEL
import numpy as np
import shelve
from scipy import io
import os


# Modes: "System" (standard), "Dark", "Light"
ctk.set_appearance_mode("System")
# Themes: "blue" (standard), "green", "dark-blue"
ctk.set_default_color_theme("dark-blue")


class RecordingApp(ctk.CTk):
    '''
    App for recording data from both pucks

    This app allows you to record multiple times and name each file name and
    data file names in the app. This is very similar to the script to make log
    files, but is faster to use.

    Attributes
    ----------
    keep_running: bool
        Boolean for checking if data logging should continue
    puck_logger: PuckLogger object
        An instance of the PuckLogger object which handles the recording of the
        data
    title: str
        Name of the app
    blue_puck_rotational_acceleration_frame:  PuckFileName object
        CTKFrame for getting the blue puck's rotational accelerometer data
    blue_puck_gyroscope_frame:  PuckFileName object
        CTKFrame for getting the blue puck's gyroscope data
    blue_puck_linear_acceleration_frame:  PuckFileName object
        CTKFrame for getting the blue puck's linear acceleration data
    blue_puck_load_cell_frame:  PuckFileName object
        CTKFrame for getting the blue puck's load cell data
    blue_puck_quaternion_frame:  PuckFileName object
        CTKFrame for getting the blue puck's quaternion data
    yellow_puck_rotational_acceleration_frame:  PuckFileName object
        CTKFrame for getting the blue puck's rotational accelerometer data
    yellow_puck_gyroscope_frame:  PuckFileName object
        CTKFrame for getting the blue puck's gyroscope data
    yellow_puck_linear_acceleration_frame:  PuckFileName object
        CTKFrame for getting the blue puck's linear acceleration data
    yellow_puck_load_cell_frame:  PuckFileName object
        CTKFrame for getting the blue puck's load cell data
    yellow_puck_quaternion_frame:  PuckFileName object
        CTKFrame for getting the blue puck's quaternion data
    file_name_textbox: CTkEntry
        One line text box to enter the overall file name
    recording_time_textbox: CTkEntry
        One line text box to enter the recording time in minutes
    file_name: str
        String extracted from the file_name_textbox

    Methods
    -------
    __init__()
        Create the recording app
    start_button_callback()
        Start recording data from the pucks
    get_data()
        Record the data on each sample time step
    stop_button_callback()
        Tells the app to stop recording and disconnects for the pucks
    write_data()
        Writes the logged data to a python dictionary and .mat file
    set_recording_length()
        Finds the total recording time and initializes the pucks' data arrays

    See Also
    --------
    log_puck_data.py
        The definition of the PuckLogger class
    '''
    def __init__(self, puck_logger: PuckLogger) -> None:
        '''
        Create the recording app

        Creates name fields for the puck data types and fields for the data
        file name and recording length.

        Parameters
        ----------
        puck_logger: PuckLogger object
            An instance of the PuckLogger object which handles the recording of
            the data
        '''
        super().__init__()  # allows access to ctk methods

        self.keep_running = False

        self.puck_logger = puck_logger

        # configure window
        self.title("FitMi Puck Data Logging App")
        self.geometry(f"{410}x{550}")

        # configure grid layout (5x2)
        self.grid_columnconfigure((0, 1), weight=0)
        self.grid_rowconfigure((0, 1, 2, 3, 4), weight=0)

        # Create the blue puck data inputs
        self.blue_puck_rotational_acceleration_frame =\
            PuckFileName(self, puck_sensor_name="Blue Puck Rotational"
                         " Accelerometer",
                         puck_file_name="puck_0_rotational_acceleration")
        self.blue_puck_rotational_acceleration_frame.grid(row=0, column=0,
                                                          padx=10, pady=10)

        self.blue_puck_gyroscope_frame =\
            PuckFileName(self, puck_sensor_name="Blue Puck Gyroscope",
                         puck_file_name="puck_0_gyroscope")
        self.blue_puck_gyroscope_frame.grid(row=1, column=0, padx=10,
                                            pady=10)

        self.blue_puck_linear_acceleration_frame =\
            PuckFileName(self, puck_sensor_name="Blue Puck Linear"
                         " Acceleration",
                         puck_file_name="puck_0_linear_acceleration")
        self.blue_puck_linear_acceleration_frame.grid(row=2, column=0, padx=10,
                                                      pady=10)

        self.blue_puck_load_cell_frame =\
            PuckFileName(self, puck_sensor_name="Blue Puck Load Cell",
                         puck_file_name="puck_0_load_cell")
        self.blue_puck_load_cell_frame.grid(row=3, column=0, padx=10,
                                            pady=10)

        self.blue_puck_quaternion_frame =\
            PuckFileName(self, puck_sensor_name="Blue Puck Quaternion",
                         puck_file_name="puck_0_quaternion")
        self.blue_puck_quaternion_frame.grid(row=4, column=0, padx=10,
                                             pady=10)

        # Create the yellow puck data inputs
        self.yellow_puck_rotational_acceleration_frame =\
            PuckFileName(self, puck_sensor_name="Yellow Puck Rotational"
                         " Accelerometer",
                         puck_file_name="puck_1_rotational_acceleration")
        self.yellow_puck_rotational_acceleration_frame.grid(row=0, column=1,
                                                            padx=10, pady=10)

        self.yellow_puck_gyroscope_frame =\
            PuckFileName(self, puck_sensor_name="Yellow Puck Gyroscope",
                         puck_file_name="puck_1_gyroscope")
        self.yellow_puck_gyroscope_frame.grid(row=1, column=1, padx=10,
                                              pady=10)

        self.yellow_puck_linear_acceleration_frame =\
            PuckFileName(self,
                         puck_sensor_name="Yellow Puck Linear Acceleration",
                         puck_file_name="puck_1_linear_acceleration")
        self.yellow_puck_linear_acceleration_frame.grid(row=2, column=1,
                                                        padx=10, pady=10)

        self.yellow_puck_load_cell_frame =\
            PuckFileName(self, puck_sensor_name="Yellow Puck Load Cell",
                         puck_file_name="puck_1_load_cell")
        self.yellow_puck_load_cell_frame.grid(row=3, column=1, padx=10,
                                              pady=10)

        self.yellow_puck_quaternion_frame =\
            PuckFileName(self, puck_sensor_name="Yellow Puck Quaternion",
                         puck_file_name="puck_1_quaternion")
        self.yellow_puck_quaternion_frame.grid(row=4, column=1, padx=10,
                                               pady=10)

        # Create the start recording button
        start_button = ctk.CTkButton(self, text="Start Recording",
                                     command=self.start_button_callback)
        start_button.grid(row=5, column=0, padx=5,
                          pady=5)

        # Create the stop recording button
        stop_button = ctk.CTkButton(self, text="Stop Recording",
                                    command=self.stop_button_callback)
        stop_button.grid(row=6, column=0, padx=5,
                         pady=5)

        self.file_name_textbox = ctk.CTkEntry(self, width=165, height=10,
                                              placeholder_text="File Name")
        self.file_name_textbox.grid(row=5, column=1, padx=10, pady=5)

        self.recording_time_textbox =\
            ctk.CTkEntry(self, width=165, height=10,
                         placeholder_text="Recording Time in Minutes")
        self.recording_time_textbox.grid(row=6, column=1, padx=10, pady=5)

        self.after(int(1000 / self.puck_logger.samples_per_second),
                   self.get_data)

    def start_button_callback(self) -> None:
        '''
        Start recording data from the pucks
        '''
        # get text from line 0 character 0 till the end before the new line
        # character
        self.file_name = self.file_name_textbox.get()
        if not self.file_name:
            tk.messagebox.showwarning(title="Missing File Name!",
                                      message="You need a data file name!")
            return

        if self.set_recording_length():
            # Start communication to each puck
            self.puck_logger.puck.open()
            self.puck_logger.puck.send_command(0, SENDVEL, 0x00, 0x01)
            self.puck_logger.puck.send_command(1, SENDVEL, 0x00, 0x01)

            print("Recording Data")
            self.puck_logger.samples_taken = 0
            self.keep_running = True

    def get_data(self) -> None:
        '''
        Record the data on each sample time step
        '''
        if self.keep_running and (self.puck_logger.samples_taken <
                                  self.puck_logger.max_samples):
            self.puck_logger.puck.checkForNewPuckData()
            self.puck_logger.store_data(self.puck_logger.puck.puck_0_packet,
                                        self.puck_logger.puck.puck_1_packet)

        self.after(int(1000/self.puck_logger.samples_per_second),
                   self.get_data)

    def stop_button_callback(self) -> None:
        '''
        Tells the app to stop recording and disconnects for the pucks
        '''
        print("Recording Stopped")
        self.keep_running = False
        # disconnects from the pucks and closes the connection to the dongle
        self.puck_logger.puck.send_command(0, SENDVEL, 0x00, 0x00)
        self.puck_logger.puck.send_command(1, SENDVEL, 0x00, 0x00)
        self.puck_logger.puck.close()

        # save the log file
        self.write_data()

    def write_data(self) -> None:
        '''
        Writes the logged data to a python dictionary and .mat file

        Saves the python data into a dictionary and then converts that into a
        self saved to the data folder. That shelf is then converted to a .mat
        file.
        '''
        # crop away any unused space.
        if self.puck_logger.samples_taken < self.puck_logger.max_samples:
            self.puck_logger.puck_0_rotational_acceleration =\
                self.puck_logger.\
                puck_0_rotational_acceleration[0:self.
                                               puck_logger.samples_taken, :]
            self.puck_logger.puck_0_gyroscope =\
                self.puck_logger.\
                puck_0_gyroscope[0:self.puck_logger.samples_taken, :]
            self.puck_logger.puck_0_linear_acceleration =\
                self.puck_logger.\
                puck_0_linear_acceleration[0:self.puck_logger.samples_taken, :]
            self.puck_logger.puck_0_load_cell =\
                self.puck_logger.\
                puck_0_load_cell[0:self.puck_logger.samples_taken, :]
            self.puck_logger.puck_0_quaternion =\
                self.puck_logger.\
                puck_0_quaternion[0:self.puck_logger.samples_taken, :]

            self.puck_logger.puck_1_rotational_acceleration =\
                self.puck_logger.\
                puck_1_rotational_acceleration[0:self.
                                               puck_logger.samples_taken, :]
            self.puck_logger.puck_1_gyroscope =\
                self.puck_logger.\
                puck_1_gyroscope[0:self.puck_logger.samples_taken, :]
            self.puck_logger.puck_1_linear_acceleration =\
                self.puck_logger.\
                puck_1_linear_acceleration[0:self.puck_logger.samples_taken, :]
            self.puck_logger.puck_1_load_cell =\
                self.puck_logger.\
                puck_1_load_cell[0:self.puck_logger.samples_taken, :]
            self.puck_logger.puck_1_quaternion =\
                self.puck_logger.\
                puck_1_quaternion[0:self.puck_logger.samples_taken, :]

        data_dictionary = {
            self.blue_puck_rotational_acceleration_frame.get_text():
                self.puck_logger.puck_0_rotational_acceleration,
            self.blue_puck_gyroscope_frame.get_text():
                self.puck_logger.puck_0_gyroscope,
            self.blue_puck_linear_acceleration_frame.get_text():
                self.puck_logger.puck_0_linear_acceleration,
            self.blue_puck_load_cell_frame.get_text():
                self.puck_logger.puck_0_load_cell,
            self.blue_puck_quaternion_frame.get_text():
                self.puck_logger.puck_0_quaternion,

            self.yellow_puck_rotational_acceleration_frame.get_text():
                self.puck_logger.puck_1_rotational_acceleration,
            self.yellow_puck_gyroscope_frame.get_text():
                self.puck_logger.puck_1_gyroscope,
            self.yellow_puck_linear_acceleration_frame.get_text():
                self.puck_logger.puck_1_linear_acceleration,
            self.yellow_puck_load_cell_frame.get_text():
                self.puck_logger.puck_1_load_cell,
            self.yellow_puck_quaternion_frame.get_text():
                self.puck_logger.puck_1_quaternion
            }

        # creates the path to the log file self
        data_shelf_name = os.path.join(self.puck_logger.data_folder,
                                       self.file_name+".shelve")

        # creates the data folder if it did not exist
        if not os.path.exists(self.puck_logger.data_folder):
            os.makedirs(self.puck_logger.data_folder)

        # saves the data into the data self
        data_shelf = shelve.open(data_shelf_name)
        for key in data_dictionary.keys():
            data_shelf[key] = data_dictionary[key]
        data_shelf.close()

        # saves the data self into a .mat file
        mat_path = os.path.join(self.puck_logger.data_folder,
                                self.file_name+".mat")
        io.savemat(mat_path, data_dictionary, appendmat=False)

    def set_recording_length(self) -> bool:
        '''
        Finds the total recording time and initializes the pucks' data arrays

        Asks the user to a recording time and finds the amount of samples to
        record based on the sample rate to achieve that length of recording.
        Based on this, the data arrays for each puck are initialized. The
        maximum amount of recording time is 1 hour.

        Returns
        -------
        bool
            Returns if the recording length was set correctly
        '''
        # get text from line 0 character 0 till the end before the new line
        # character
        recording_length_string = self.recording_time_textbox.get()

        # Ask the user for a recording length until they enter a number
        try:
            recording_length_minutes =\
                    float(recording_length_string)
        except ValueError:
            tk.messagebox.showwarning(title="Incorrect time format.",
                                      message="You need to input a number!")
            return False

        if (recording_length_minutes > 60) or (recording_length_minutes < 0):
            tk.messagebox.showwarning(title="Recording time out of range",
                                      message="Please enter a number above 0"
                                      " and below 60.")
            return False

        max_samples_needed =\
            int(recording_length_minutes * 60 *
                self.puck_logger.samples_per_second)
        self.puck_logger.max_samples = max_samples_needed

        # initialize the data arrays of each puck to the total number of
        # samples needed
        self.puck_logger.puck_0_rotational_acceleration =\
            np.zeros([max_samples_needed, 3])
        self.puck_logger.puck_0_gyroscope = np.zeros([max_samples_needed, 3])
        self.puck_logger.puck_0_linear_acceleration =\
            np.zeros([max_samples_needed, 3])
        self.puck_logger.puck_0_load_cell = np.zeros([max_samples_needed, 1])
        self.puck_logger.puck_0_quaternion = np.zeros([max_samples_needed, 4])

        self.puck_logger.puck_1_rotational_acceleration =\
            np.zeros([max_samples_needed, 3])
        self.puck_logger.puck_1_gyroscope = np.zeros([max_samples_needed, 3])
        self.puck_logger.puck_1_linear_acceleration =\
            np.zeros([max_samples_needed, 3])
        self.puck_logger.puck_1_load_cell = np.zeros([max_samples_needed, 1])
        self.puck_logger.puck_1_quaternion = np.zeros([max_samples_needed, 4])

        return True


class PuckFileName(ctk.CTkFrame):
    '''
    Defines the frame for recording data file names

    Pairs a sensor title with a data file name. This is meant for each of the
    pucks sensors and allow you to get the file name from the text box with a
    get function

    Attributes
    ----------
    puck_sensor_name: str
        The name of the sensor used for the title of this frame
    title: CTKLabel
        The label of the frame
    file_name_textbox: CTkEntry
        One line text box to enter the data's name
    file_name: str
        The default name in the file_name_textbox

    Methods
    -------
    get_text
        Extracts out the file names from the text box
    '''
    def __init__(self, *args, puck_sensor_name: str,
                 puck_file_name: str, **kwargs) -> None:
        '''
        Creates the data entry box with a title

        Parameters
        ----------
        *args
            Any non keyword arguments for the super CTKFrame class
        puck_sensor_name: str
            The name of the sensor
        puck_file_name: str
            The name of the data file
        **kwargs
            Any other keyword arguments not specified for the super CTKFrame
            class
        '''
        super().__init__(*args, **kwargs)
        # setup the label of the frame
        self.puck_sensor_name = puck_sensor_name
        self.title = ctk.CTkLabel(self, text=self.puck_sensor_name, width=165)
        self.title.grid(row=0, column=0)

        # setup the file name entry
        self.file_name = puck_file_name
        self.file_name_textbox =\
            ctk.CTkEntry(self, height=10, placeholder_text=self.file_name,
                         width=165)
        self.file_name_textbox.insert(0, self.file_name)
        self.file_name_textbox.grid(row=1, column=0, padx=10, pady=10)

    def get_text(self) -> None:
        '''
        Extracts out the file names from the text box
        '''
        # get text from line 0 character 0 till the end before the new line
        # character
        return self.file_name_textbox.get()


if __name__ == "__main__":
    puck_logger_object = PuckLogger(using_app=True)
    app = RecordingApp(puck_logger=puck_logger_object)
    try:
        app.mainloop()
    finally:
        app.stop_button_callback()
