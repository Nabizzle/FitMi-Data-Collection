import os
import shelve
import numpy as np
from scipy import io
import threading
import time
from Puck.hid_puck import HIDPuckDongle, SENDVEL
from Puck.puck_packet import PuckPacket


class PuckLogger(object):
    '''
    Saves puck data as a dictionary and .mat file

    Saves the base data from each puck, the acceleration, gyroscope, linear
    acceleration, load cell, and quaternion, as a python dictionary and then
    a .mat file. This class when run also allows you to stop the recording
    early by pressing enter in the console.

    Attributes
    ----------
    data_folder:str
        The path to the data folder. It has to be named data and he a subfolder
        in the current working directory
    file_name:string
        The name of the log file
    samples_per_second:int
        The number os samples added to the data variables per second
    keep_running:bool
        Indicates if the recording should end early
    puck:HIDPuckDongle object
        Communication class with the FitMi dongle
    samples_taken:int
        Keeps a running total of the number of samples
    max_samples:int
        The total number of samples desired
    puck_0_acceleration:List[int]
        Data variable for the blue puck's accelerometer values
    puck_0_gyroscope:List[int]
        Data variable for the blue puck's gyroscope values
    puck_0_linear_acceleration:List[int]
        Data variable for the blue puck's linear acceleration values
    puck_0_load_cell:List[int]
        Data variable for the blue puck's load cell value
    puck_0_quaternion:List[int]
        Data variable for the blue puck's quaternion values
    puck_1_acceleration:List[int]
        Data variable for the yellow puck's accelerometer values
    puck_1_gyroscope:List[int]
        Data variable for the yellow puck's gyroscope values
    puck_1_linear_acceleration:List[int]
        Data variable for the yellow puck's linear acceleration values
    puck_1_load_cell:List[int]
        Data variable for the yellow puck's load cell value
    puck_1_quaternion:List[int]
        Data variable for the yellow puck's quaternion values
    check_stop_thread:threading.Thread thread
        Thread to check of the user has pressed enter to stop data collection
    check_stop_thread.daemon:bool
        Sets if the thread stops with the main function (True) or not

    Methods
    -------
    __init__()
        Initializes the variables needed to record into a log file
    check_stop()
        Asks the user to press enter to stop recording.
    run()
        Setup the length of recording and stores the data on each sample step.
    set_filename()
        Ask the user for the log file's name
    set_recording_length()
        Finds the total recording time and initializes the pucks' data arrays
    store_data(puck_0_packet, puck_1_packet)
        Extracts each data type from the pucks total data.
    write_data()
        Writes the logged data to a python dictionary and .mat file
    stop()
        Closes communication with the pucks and saves the log file data
    '''
    def __init__(self, using_app=False) -> None:
        '''
        Initializes the variables needed to record into a log file

        Creates the path to where the log file will be stored, sets up what is
        needed to communicate and log all of the pucks' data into variables,
        and sets up the thread looking to see if the user wants to stop
        recording early.

        Parameters
        ----------
        using_app:bool
            boolean for if an app is used instead of the script
        '''
        self.data_folder = os.path.join(os.getcwd(), "data")
        self.file_name = "temp"

        self.samples_per_second = 50
        self.keep_running = True
        self.puck = HIDPuckDongle()

        self.samples_taken = 0
        self.max_samples = None

        self.puck_0_acceleration = None
        self.puck_0_gyroscope = None
        self.puck_0_linear_acceleration = None
        self.puck_0_load_cell = None
        self.puck_0_quaternion = None

        self.puck_1_acceleration = None
        self.puck_1_gyroscope = None
        self.puck_1_linear_acceleration = None
        self.puck_1_load_cell = None
        self.puck_1_quaternion = None

        if not using_app:
            self.check_stop_thread = threading.Thread(target=self.check_stop)
            self.check_stop_thread.daemon = True

    def check_stop(self) -> None:
        '''
        Asks the user to press enter to stop recording.

        Asks the user to press enter to stop logging data. The user can enter
        anything they want into the console to stop recording. This is just a
        thread that will change the check_stop_thread variable to False when it
        completes.
        '''
        while self.keep_running:
            _ = input("press enter to stop logging.")
            self.keep_running = False

    def run(self) -> None:
        '''
        Setup the length of recording and stores the data on each sample step.

        Sets up the recording location and connection to the pucks. Then
        records data according to the sample rate and trims off the end of the
        data arrays if they were unused. This occurs when stopping the
        recording early.
        '''
        # Set up how long to record and where to record to
        self.set_recording_length()
        self.set_filename()

        # Start communication to each puck
        self.puck.open()
        self.puck.send_command(0, SENDVEL, 0x00, 0x01)
        self.puck.send_command(1, SENDVEL, 0x00, 0x01)

        print("recording data")
        # Start the thread looking for the recording to stop early
        self.check_stop_thread.start()
        self.samples_taken = 0

        # Record data according to the sample rate
        while self.keep_running and (self.samples_taken < self.max_samples):
            self.puck.checkForNewPuckData()
            self.store_data(self.puck.puck_0_packet, self.puck.puck_1_packet)
            time.sleep(1.0/self.samples_per_second)

        # crop away any unused space.
        if self.samples_taken < self.max_samples:
            self.puck_0_acceleration =\
                self.puck_0_acceleration[0:self.samples_taken, :]
            self.puck_0_gyroscope =\
                self.puck_0_gyroscope[0:self.samples_taken, :]
            self.puck_0_linear_acceleration =\
                self.puck_0_linear_acceleration[0:self.samples_taken, :]
            self.puck_0_load_cell =\
                self.puck_0_load_cell[0:self.samples_taken, :]
            self.puck_0_quaternion =\
                self.puck_0_quaternion[0:self.samples_taken, :]

            self.puck_1_acceleration =\
                self.puck_1_acceleration[0:self.samples_taken, :]
            self.puck_1_gyroscope =\
                self.puck_1_gyroscope[0:self.samples_taken, :]
            self.puck_1_linear_acceleration =\
                self.puck_1_linear_acceleration[0:self.samples_taken, :]
            self.puck_1_load_cell =\
                self.puck_1_load_cell[0:self.samples_taken, :]
            self.puck_1_quaternion =\
                self.puck_1_quaternion[0:self.samples_taken, :]

    def set_filename(self) -> None:
        '''
        Ask the user for the log file's name
        '''
        self.file_name = input("enter a name for the datafile: ")

    def set_recording_length(self) -> None:
        '''
        Finds the total recording time and initializes the pucks' data arrays

        Asks the user to a recording time and finds the amount of samples to
        record based on the sample rate to achieve that length of recording.
        Based on this, the data arrays for each puck are initialized
        '''
        # boolean to check if the user input a valid recording length
        correct_input_format = False
        recording_length_message =\
            "how long would you like to record (in minutes)? "
        recording_length_minutes = -1

        # Ask the user for a recording length until they enter a number
        while not correct_input_format:
            try:
                recording_length_minutes =\
                     float(input(recording_length_message))
            except ValueError:
                print("you need to input a number")

            if (recording_length_minutes > 60) or\
               (recording_length_minutes < 0):
                print("please enter a number between 0 and 60")
                correct_input_format = False
            else:
                correct_input_format = True

        max_samples_needed =\
            int(recording_length_minutes * 60 * self.samples_per_second)
        self.max_samples = max_samples_needed

        # initialize the data arrays of each puck to the total number of
        # samples needed
        self.puck_0_acceleration = np.zeros([max_samples_needed, 3])
        self.puck_0_gyroscope = np.zeros([max_samples_needed, 3])
        self.puck_0_linear_acceleration = np.zeros([max_samples_needed, 3])
        self.puck_0_load_cell = np.zeros([max_samples_needed, 1])
        self.puck_0_quaternion = np.zeros([max_samples_needed, 4])

        self.puck_1_acceleration = np.zeros([max_samples_needed, 3])
        self.puck_1_gyroscope = np.zeros([max_samples_needed, 3])
        self.puck_1_linear_acceleration = np.zeros([max_samples_needed, 3])
        self.puck_1_load_cell = np.zeros([max_samples_needed, 1])
        self.puck_1_quaternion = np.zeros([max_samples_needed, 4])

    def store_data(self, puck_0_packet: PuckPacket,
                   puck_1_packet: PuckPacket) -> None:
        '''
        Extracts each data type from the pucks total data.

        Saves each puck's PuckPacket class variables for the accelerometer,
        gyroscope, linear acceleration, load_cell, and quaternion. Then the
        sample number is incremented.

        Parameters
        ----------
        puck_0_packet:PuckPacket object
            Contains the polled data from the blue puck
        puck_1_packet:PuckPacket object
            Contains the polled data from the yellow puck
        '''
        self.puck_0_acceleration[self.samples_taken, :] =\
            puck_0_packet.accelerometer
        self.puck_0_gyroscope[self.samples_taken, :] = puck_0_packet.gyroscope
        self.puck_0_linear_acceleration[self.samples_taken, :] =\
            puck_0_packet.linear_acceleration
        self.puck_0_load_cell[self.samples_taken, :] =\
            puck_0_packet.load_cell
        self.puck_0_quaternion[self.samples_taken, :] =\
            puck_0_packet.quaternion

        self.puck_1_acceleration[self.samples_taken, :] =\
            puck_1_packet.accelerometer
        self.puck_1_gyroscope[self.samples_taken, :] = puck_1_packet.gyroscope
        self.puck_1_linear_acceleration[self.samples_taken, :] =\
            puck_1_packet.linear_acceleration
        self.puck_1_load_cell[self.samples_taken, :] = puck_1_packet.load_cell
        self.puck_1_quaternion[self.samples_taken, :] =\
            puck_1_packet.quaternion

        self.samples_taken += 1  # increment the sample number

    def write_data(self) -> None:
        '''
        Writes the logged data to a python dictionary and .mat file

        Saves the python data into a dictionary and then converts that into a
        self saved to the data folder. That shelf is then converted to a .mat
        file.
        '''
        data_dictionary = {
            "puck_0_acceleration": self.puck_0_acceleration,
            "p0_gyroscope": self.puck_0_gyroscope,
            "p0_linear_acceleration": self.puck_0_linear_acceleration,
            "p0_load_cell": self.puck_0_load_cell,
            "p0_quaternion": self.puck_0_quaternion,

            "puck_1_acceleration": self.puck_1_acceleration,
            "p1_gyroscope": self.puck_1_gyroscope,
            "p1_linear_acceleration": self.puck_1_linear_acceleration,
            "p1_load_cell": self.puck_1_load_cell,
            "p1_quaternion": self.puck_1_quaternion
            }

        # creates the path to the log file self
        data_shelf_name = os.path.join(self.data_folder,
                                       self.file_name+".shelve")

        # creates the data folder if it did not exist
        if not os.path.exists(self.data_folder):
            os.makedirs(data_shelf_name)

        # saves the data into the data self
        data_shelf = shelve.open(data_shelf_name)
        for key in data_dictionary.keys():
            data_shelf[key] = data_dictionary[key]
        data_shelf.close()

        # saves the data self into a .mat file
        mat_path = os.path.join(self.data_folder, self.file_name+".mat")
        io.savemat(mat_path, data_dictionary, appendmat=False)

    def stop(self) -> None:
        '''
        Closes communication with the pucks and saves the log file data
        '''
        # disconnects from the pucks and closes the connection to the dongle
        self.puck.send_command(0, SENDVEL, 0x00, 0x00)
        self.puck.send_command(1, SENDVEL, 0x00, 0x00)
        self.puck.close()

        # save the log file
        self.write_data()
        try:
            self.check_stop_thread.join(2)  # stop the thread after 2 seconds
        except Exception:
            pass


if __name__ == "__main__":
    '''
    Start data collection
    '''
    puck_logger = PuckLogger()
    try:
        puck_logger.run()
    finally:
        puck_logger.stop()
