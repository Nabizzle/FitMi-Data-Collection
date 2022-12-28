import tkinter as tk
from tkinter import ttk
import time
import threading
import random
import queue
import matplotlib
import numpy
import sys
import matplotlib.animation as animation
import datetime

from tkinter import StringVar

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

from Puck import HIDPuckDongle
from Puck.hid_puck import *

#This is the UI part of the app
class MainApp:

    def __init__(self, gui, random_number_gen):
        #Get a handle to the user-interface
        self.gui = gui

        #Add a combo-box to the user interface
        self.selected_value = StringVar()
        self.selection_box = ttk.Combobox(self.gui, textvariable=self.selected_value, state='readonly')
        self.selection_box['values'] = ('Loadcell', \
                                        'Accelerometer (x)', 'Accelerometer (y)', 'Accelerometer (z)', \
                                        'Gyrometer (x)', 'Gyrometer (y)', 'Gyrometer (z)', \
                                        'Magnetometer (x)', 'Magnetometer (y)', 'Magnetometer (z)', \
                                        'Velocity (x)', 'Velocity (y)', 'Velocity (z)' )
        self.selection_box.current(0)
        self.selection_box.pack()

        #Add a button to signal that we want to start a new trial
        self.start_trial_button = tk.Button(self.gui, text='Start New Trial', command=self.start_trial_button_command)
        self.start_trial_button.pack()

        #Add a label to signal when VNS is occurring
        self.vns_label = tk.Label(self.gui, text='Waiting for VNS signal...')
        self.vns_label.pack()

        #Create buffers to store all of the streaming data
        self.plot_buffer = numpy.zeros((1, 200)).tolist()[0]

        #Create a figure
        self.canvas_fig = plt.figure(1)
        Fig = matplotlib.figure.Figure(figsize=(5, 4), dpi=100)

        #Create a subplot
        FigSubPlot = Fig.add_subplot(1, 1, 1)
        x_data = range(len(self.plot_buffer))
        y_data = self.plot_buffer
        self.plot_line, = FigSubPlot.plot(x_data, y_data, 'r-')
            
        #Get the figure canvas
        self.plot_canvas = FigureCanvasTkAgg(Fig, master=self.gui)

        #Display the figure canvas
        self.plot_canvas.show()

        #Layout the figure canvas on the window
        self.plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.plot_canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        ax = self.plot_canvas.figure.axes[0]
        ax.set_xlim(0, 200)
        ax.set_ylim(0, 1024)

        #Update the gui
        self.gui.update()
        
        #Create protocol for handling the window closing
        self.gui.protocol("WM_DELETE_WINDOW", self.end_application)

        #Get the random number generator
        self.rand = random_number_gen

        self.start_time = datetime.datetime.now()
        self.end_time = datetime.datetime.now()
        self.loop_count = 0

        #Make an instance of the background thread
        self.background_thread = BackgroundThread()

        #Start a periodic call on the GUI thread to check for updates form the background thread
        self.periodic_gui_update()


    def process_incoming_data(self):
        while self.background_thread.msg_queue_background_to_foreground.qsize():
            try:
                new_data = []
                with self.background_thread.msg_queue_background_to_foreground.mutex:
                    new_data = list(self.background_thread.msg_queue_background_to_foreground.queue)
                    self.background_thread.msg_queue_background_to_foreground.queue.clear()
                self.plot_buffer.extend(new_data)
            except Queue.Empty:
                pass

        #Keep plot buffer to 200 elements
        plot_buf_len = len(self.plot_buffer)
        if plot_buf_len > 200:
            num_to_cut = plot_buf_len - 200
            self.plot_buffer = self.plot_buffer[num_to_cut:]

        y_data = self.plot_buffer
        x_data = range(len(y_data))

        self.plot_line.set_data(x_data, y_data)
        self.plot_canvas.draw()

        #Determine whether to indicate that VNS is active or not active
        with self.background_thread.vns_active_mutex:
            if self.background_thread.vns_active:
                self.vns_label['text'] = 'VNS Active'
                self.vns_label['fg'] = 'green'
            else:
                self.vns_label['text'] = 'Waiting for VNS signal...'
                self.vns_label['fg'] = 'black'

        self.loop_count += 1
        self.end_time = datetime.datetime.now()
        diff_time = self.end_time - self.start_time
        total_seconds = diff_time.total_seconds()
        if (total_seconds >= 1.0):
            #print self.loop_count
            self.loop_count = 0
            self.start_time = self.end_time

    def periodic_gui_update(self):
        #Process any new data that has come in from the background thread
        self.process_incoming_data()

        #Add the currently selected value to the msg queue
        self.background_thread.msg_queue_foreground_to_background.put(self.selected_value)

        #Check the "is_running" flag. If not running, exit the program
        if not self.background_thread.is_running:
            sys.exit(1)

        #Make sure to to a periodic check on the GUI every 33 ms
        self.gui.after(10, self.periodic_gui_update)

    def end_application(self):
        self.background_thread.shutdown_background_thread()

    def start_trial_button_command(self):
        with self.background_thread.initiate_trial_mutex:
            self.background_thread.initiate_trial = True

class Trial:
    def __init__(self):
        self.signal = []
        self.vns = 0

class Session:
    def __init__(self):
        self.trials = []
        self.vns_threshold = 0

    def determine_new_vns_threshold(self):
        max_of_each_trial = []
        for t in self.trials:
            max_of_each_trial.append(max(t.signal))
        self.vns_threshold = sum(max_of_each_trial) / len(max_of_each_trial)

#This is the background process part of the app
class BackgroundThread:
    def __init__(self):
        #Create a session
        self.session = Session()
        self.session_mutex = threading.Lock()

        self.vns_active = False
        self.vns_active_mutex = threading.Lock()

        #Connect to the pucks
        self.puck = HIDPuckDongle()
        self.puck.open()
        self.puck.sendCommand(0, 0x10, 0x00, 0x01)
        self.puck.sendCommand(1, 0x10, 0x00, 0x01)
        self.puck.checkForNewPuckData()
        self.puck_data_1 = self.puck.puck_packet_0

        self.is_running = 1
        self.msg_queue_foreground_to_background = Queue.Queue()
        self.msg_queue_background_to_foreground = Queue.Queue()

        self.initiate_trial = False
        self.initiate_trial_mutex = threading.Lock()
        self.trial_state = -1
        self.current_trial = Trial()

        #Create and start the background thread
        self.background_thread = threading.Thread(target=self.background_thread_function)
        self.background_thread.start()

    def shutdown_background_thread(self):
        self.is_running = 0
        self.puck.sendCommand(0, 0x10, 0x00, 0x00)
        self.puck.sendCommand(1, 0x10, 0x00, 0x00)
        self.puck.close()

    def background_thread_function(self):
        #Loop as long as the program is running
        selected_string = ''
        new_selected_string = ''

        while self.is_running:
            
            while self.msg_queue_foreground_to_background.qsize():
                try:
                    with self.msg_queue_foreground_to_background.mutex:
                        item_queue = list(self.msg_queue_foreground_to_background.queue)
                        if len(item_queue) > 0:
                            new_selected_string = item_queue[0].get()
                            if new_selected_string is not None:
                                if new_selected_string != '':
                                    if new_selected_string != selected_string:
                                        #Remember the sensor the user selected
                                        selected_string = new_selected_string
                                        #Clear the list of trials for this session and start fresh
                                        self.session.trials = []
                                        self.current_trial = Trial()
                                        self.trial_state = -1

                        self.msg_queue_foreground_to_background.queue.clear()
                except Queue.Empty:
                    pass

            #Add random numbers to the queue
            #new_num = rand.randint(-10, 10)
            self.puck.checkForNewPuckData()
            self.puck_data_1 = self.puck.puck_packet_0

            #Check to see what data we need to send back to the GUI
            new_streaming_data = 0
            if (selected_string == 'Accelerometer (x)'):
                new_streaming_data = self.puck_data_1.accelerometer[0, 0]
            elif (selected_string == 'Accelerometer (y)'):
                new_streaming_data = self.puck_data_1.accelerometer[0, 1]
            elif (selected_string == 'Accelerometer (z)'):
                new_streaming_data = self.puck_data_1.accelerometer[0, 2]
            elif (selected_string == 'Gyrometer (x)'):
                new_streaming_data = self.puck_data_1.gyroscope[0, 0]
            elif (selected_string == 'Gyrometer (y)'):
                new_streaming_data = self.puck_data_1.gyroscope[0, 1]
            elif (selected_string == 'Gyrometer (z)'):
                new_streaming_data = self.puck_data_1.gyroscope[0, 2]
            elif (selected_string == 'Magnetometer (x)'):
                new_streaming_data = self.puck_data_1.magnetometer[0, 0]
            elif (selected_string == 'Magnetometer (y)'):
                new_streaming_data = self.puck_data_1.magnetometer[0, 1]
            elif (selected_string == 'Magnetometer (z)'):
                new_streaming_data = self.puck_data_1.magnetometer[0, 2]
            elif (selected_string == 'Velocity (x)'):
                new_streaming_data = self.puck_data_1.velocity[0, 0]
            elif (selected_string == 'Velocity (y)'):
                new_streaming_data = self.puck_data_1.velocity[0, 1]
            elif (selected_string == 'Velocity (z)'):
                new_streaming_data = self.puck_data_1.velocity[0, 2]
            elif (selected_string == 'Loadcell'):
                new_streaming_data = self.puck_data_1.load_cell
            
            #Send the data to the GUI for graphing purposes
            self.msg_queue_background_to_foreground.put(new_streaming_data)

            #Check to see if the user has initiated a trial
            with self.initiate_trial_mutex:
                if self.initiate_trial and self.trial_state == -1:
                    self.trial_state = 0
                    self.initiate_trial = False

            #Check the current trial state
            if self.trial_state == 0:
                #Instantiate a new trial object
                self.current_trial = Trial()
                self.trial_state = 1
            elif self.trial_state == 1:
                #Gather data for this trial
                self.current_trial.signal.append(new_streaming_data)

                #Determine whether to deliver VNS
                if (len(self.session.trials) > 1):
                    this_trial_pk = max(self.current_trial.signal)
                    if this_trial_pk >= self.session.vns_threshold:
                        with self.vns_active_mutex:
                            self.vns_active = True

                #Check to see if we have gathered enough data to complete this trial
                if (len(self.current_trial.signal) >= 200):
                    self.trial_state = 2
            elif self.trial_state == 2:
                #Turn of the VNS signal
                with self.vns_active_mutex:
                    self.vns_active = False
                #Finalize the trial, save it in the session model
                self.session.trials.append(self.current_trial)
                #Determine new vns threshold for next trial
                self.session.determine_new_vns_threshold()
                #Change the trial state to indicate that no trial is running
                self.trial_state = -1
            
            #Sleep the thread for 33 ms so that we don't consume the whole CPU
            time.sleep(0.033)


#Main function starts here
if __name__ == '__main__':
    #Initialize the random number engine
    rand = random.Random()

    #Set up the user interface by creating the main window of the program
    main_window = tk.Tk()
    main_window.geometry("500x500")
    main_window.resizable(1, 1)
    main_window.title("Hello, World!")
    
    #Start the main loop of the program
    my_app = MainApp(main_window, rand)
    main_window.mainloop()


