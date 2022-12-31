import hid
import time
import threading
import struct
import os
# suppresses pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from Puck.puck_packet import PuckPacket
import queue
from typing import Dict


# Command definitions
RBLINK       = 0x01 # Blink the red light
GBLINK       = 0x02 # Blink the green light
BBLINK       = 0x03 # Blink the blue light
RPULSE       = 0x05 # Pulse the red light
MBLINK       = 0x04 # "Blink" the motor
GPULSE       = 0x06 # Pulse the green light
BPULSE       = 0x07 # Pulse the green light
MPULSE       = 0x08 # Pulse the motor
MPUENBL      = 0x09 #
PWR          = 0x0A # Turn the puck on or off?
GAMEON       = 0x0B # Puts the puck in "game mode"
MAGCALX      = 0x0C # Send magnetometer calibration data back to puck
MAGCALY      = 0x0D # Send magnetometer calibration data back to puck
MAGCALZ      = 0x0E # Send magnetometer calibration data back to puck
DNGLRST      = 0x0F # Reset the dongle
SENDVEL      = 0x10 # Send velocity (data==1) or send magnetometer (data==0)
TOUCHBUZ     = 0x11 # Turn touch buzz on and off (1 and 0)
CHANGEFREQ   = 0x12 # Change the frequency of the RX radio
RXCHANGEFREQ = 0x13 # Change the frequency of sending data with the dongle
CHANSPY      = 0x14 # Spy on a channel
SETUSBPIPES  = 0x15 # Tell the dongle which pipes to send over usb

# Dictionary for addressing the lights or motor blinking and pulsing
COMMANDS = {"red": {"blink": RBLINK, "pulse": RPULSE},
            "green": {"blink": GBLINK, "pulse": GPULSE},
            "blue": {"blink": BBLINK, "pulse": BPULSE},
            "motor": {"blink": MBLINK, "pulse": MPULSE}}


class HIDPuckDongle(object):
    '''
    Defines how to communicate to and from the pucks

    Attributes
    ----------
    VENDOR_ID : int
        The vendor id of the dongle in the hardware input device list. Make
        sure this number does not change or else the dongle will not be
        connected to.
    PRODUCT_ID : int
        The product id of the dongle in the hardware input device list. Make
        sure this number does not change or else the dongle will not be
        connected to.
    print_debug : bool
        True is the debug messages should print out
    dongle : hid.device
        A hardware input device
    is_open : bool
        Indicator for if the dongle connection has been opened
    error_report_path : file path
        A file location of logging what data has been sent
    receiving_data : bool
        An indicator for if input data is coming in
    puck_0_packet : PuckPacket object
        The data from the blue puck
    puck_1_packet : PuckPacket object
        The data from the yellow puck
    rx_hardware_state : int
        The state indicator from a received data packet
    rx_channel : int
        The channel data was received on
    block_0_pipe : int
        A three bit value indicating the pipe for the blue puck
    block_1_pipe : int
        A three bit value indicating the pipe for the yellow puck
    input_thread : threading.Thread
        A thread for checking if data has come in
    input : byte array
        A 62 bit array of read values that are parsed into the received rx and
        block variables and the data for each puck data packet.
    usb_out_queue : queue.Queue
        A queue of commands to send over usb
    touch_queue : queue.Queue
        A queue of touch events in pairs of the puck number (blue = 0,
        yellow = 1) and then a boolean for if there was a touch
    last_sent : List[float]
        The last time an actuate command was sent to either puck. The first
        index is for the blue puck and the second is for the yellow puck

    Methods
    -------
    __init__(error_report)
        Setup threads and variables for communicating with the pucks
    open()
        Open the connection to the dongle
    check_connection()
        Check if the pucks are sending data or if the radio should reset
    wait_for_data()
        Check if data has been received by the input_checking thread
    input_checker()
        Thread for checking if input data is coming in
    check_for_touch(input, touch_history, puck_number)
        Parse the status byte of the input data to see if there was a touch
    checkForNewPuckData()
        Directs the incoming data the correct parsing functions
    parse_rx_data(rx_data)
        Extract out the RX radio data from the input stream
    send_command(puck_number, command, message, last_byte)
        Formats a command to one of the pucks
    note_sending(value)
        Sends a message to the error log
    actuate(puck_number, duration, amplitude, action_type, actuator)
        Sends a command to "blink" or pulse one of the lights or the motor
    set_touch_buzz(puck_number, value)
        Turns the vibration when touched feature on or off
    change_rx_freq(new_frequency)
        Changes the frequency of the RX radio
    set_usb_pipes(packet_0_pipe, packet_1_pipe)
        Tell the dongle which pipes to send over the usb connection
    start_spy(channel, duration)
        Spy on a particular channel for a specific amount of time
    stop()
        Set the is_open value to False
    close()
        Reset the puck's to default state and close the input thread
    is_opened()
        Returns the is_open variable
    is_plugged()
        Checks if the dongle is in the list of hardware input devices
    is_plugged_fast()
        Simplified is_plugged method to check if the dongle is receiving data
    get_device_info()
        Finds the hardware input device for the dongle
    '''
    def __init__(self, error_report: str = None):
        '''
        Setup threads and variables for communicating with the pucks

        Setup the threads for communicating with the pucks and the data
        variables that store communication data. Performs the relevant steps to
        set up the dongle as a hardware input device.

        Parameters
        ----------
        error_report : str, optional
            path to the error log text file

        Notes
        -----
        Do not configure the dongle as a joystick hardware input device (hid).
        pygame is used to wait in specific threads and will take control of it
        automatically.
        '''
        # set the hardware ids of the dongle
        self.VENDOR_ID = 0x04d8 # do not change this
        self.PRODUCT_ID = 0x2742 # do not change this

        self.print_debug = False

        self.dongle = hid.device()

        self.is_open = False

        # if the error report path is set, make a directory to save it in
        if error_report is not None:
            self.error_report_path = error_report
            if not os.path.exists(self.error_report_path):
                os.makedirs(self.error_report_path)
        else:
            self.error_report_path = None

        # set default values of received data attributes
        self.receiving_data = False
        self.puck_0_packet = PuckPacket()
        self.puck_1_packet = PuckPacket()
        self.rx_hardware_state = 0
        self.rx_channel = 0
        self.block_0_pipe = 0
        self.block_1_pipe = 1

        # setup the input checking thread
        self.input_thread = threading.Thread(target=self.input_checker)
        self.input = None

        # setup the queues of output data and the log of touches to the puck
        self.usb_out_queue = queue.Queue(maxsize=10)
        self.touch_queue = queue.Queue(maxsize=10)

        # instantiate the last time each puck was touched to 0
        self.last_sent = [0.0, 0.0]


    def open(self):
        '''
        Open the connection to the dongle

        Starts the dongle connection or reconnects to the dongle if it was
        already connected to. Then it puts the pucks in "game mode" and starts
        monitoring for inputs.
        '''
        # if the dongle is not found in the index of hardware input devices,
        # end the method
        if not self.is_plugged():
            return

        # if the dongle connection is already open, close the connection
        if self.print_debug:
            print("dongle open?")
        try:
            self.dongle.close()
        except:
            pass

        # connect to the dongle
        self.dongle.open(self.VENDOR_ID, self.PRODUCT_ID)
        if self.print_debug:
            print("manufacturer: %s" % self.dongle.get_manufacturer_string())
        if self.print_debug:
            print("product: %s" % self.dongle.get_product_string())

        # set the open indicator to True and monitor for inputs
        self.is_open = True
        self.input_thread.start()

        # set the plugged in state to True and check if the RX radio is working
        # and getting data
        self.plug_state = True
        self.receiving_data = False
        self.check_connection()
        self.wait_for_data()

        self.send_command(0,GAMEON, 0x00, 0x01) # puts puck 0 into game mode
        self.send_command(1,GAMEON, 0x00, 0x01) # puts puck 1 into game mode


    def check_connection(self):
        '''
        Check if the pucks are sending data or if the radio should reset
        
        Check either puck is streaming data. If not, reset the
        RX radio and wait for it to startup
        '''
        # Check if either puck has sent data at least 1 out of 200 times
        # ends the method of data is already being sent
        for i in range(0, 200):
            self.checkForNewPuckData()
            if self.puck_0_packet.connected or self.puck_1_packet.connected:
                return
            pygame.time.wait(1)
        
        # If data is not coming from the pucks, reset the radio
        self.send_command(0, DNGLRST, 0x00, 0x00)
        pygame.time.wait(600) # wait 600ms for data to come in


    def wait_for_data(self):
        '''
        Check if data has been received by the input_checking thread

        Waits about 200 ms for data to be received before moving on. This
        affects when the open method finishes and sends the command to switch
        the pucks into "game on" mode.
        '''
        for i in range(0, 200):
            pygame.time.wait(1)  # wait until we are getting data
            if self.receiving_data:
                return


    def input_checker(self):
        '''
        Tries to read in input data from the pucks

        Makes an attempt to read the input data from the pucks up to a certain
        number of times. Once a successful read happens, the pucks are checked
        for if they are being touched and usb queue is sent out
        '''
        # set the read counter variables
        read_failure_count = 0
        max_read_failures = 70

        # Create a dictionary for if the pucks have been touched
        touch_history = {"puck_0": False, "puck_1": False}

        # While the dongle is connected to, try to read in the inputs, check if
        # the pucks are touched and write out the usb queue over the dongle
        while self.is_open:
            # read in the puck data
            try:
                self.input = self.dongle.read(62)
                # if the read failed, increment the read failure counter
                if not self.input:
                    read_failure_count += 1
                    # If the reads have reached the maximum amount, indicate
                    # the connection is likely severed
                    if read_failure_count >= max_read_failures:
                        self.receiving_data = False
                else:
                    read_failure_count = 0
                    self.receiving_data = True
                    # poll for touch events on each puck
                    self.check_for_touch(self.input,
                        touch_history, puck_number=0)
                    self.check_for_touch(self.input,
                        touch_history, puck_number=1)

                # if there is data in the usb queue send it out
                if not self.usb_out_queue.empty():
                    # first byte is report id
                    self.dongle.write(self.usb_out_queue.get()) 
                    
            except Exception as e:
                self.receiving_data = False
                if self.print_debug: print(e)

            finally:
                time.sleep(0.00001) # wait in infinitesimal amount of time
                
        # clear the queue when the connection is meant to close
        for _ in range(10):
            if not self.usb_out_queue.empty():
                # first byte is report id
                self.dongle.write(self.usb_out_queue.get())
            else:
                break
        # close the connection to the dongle
        self.dongle.close()


    def check_for_touch(self, input: bytearray, touch_history: Dict[str, bool],
        puck_number: int = 0):
        '''
        Parse the status byte of the input data to see if there was a touch

        Looks at the touch bit of the status byte to see if the puck is being
        touched. If this touch value is different than the previous touch
        value, then it is added to the touch queue.

        Parameters
        ----------
        input : bytearray
            The data stream from both pucks
        touch_history : dict
            A dictionary containing if either puck was being touched the last
            time this method was called
        puck_number : int, default = 0
            The puck checked for this method. 0 is the blue puck and 1 is the
            yellow puck

        Notes
        -----
        Touch events can be too fast for the game loop to catch. Missing touch
        events can make the game feel broken. This thread runs faster than the
        game loop and makes it more likely that we will catch touch events that
        the game loop might have missed.
        '''
        # sets the index for the status byte in the input byte array
        status_byte_index = 29
        if puck_number == 1:
            status_byte_index = 59

        # sets the status byte and extracts out the touch indicator from it
        status = input[status_byte_index]
        touch = (status & 0b00000100) >> 2

        # adds True to the blue puck's touch queue if it wasn't touched before
        # and is now and adds False to the queue if it isn't being touched, but
        # is now. Each value is added with the puck number.
        if puck_number == 0:
            if touch and not touch_history["puck_0"]:
                if not self.touch_queue.full():
                    self.touch_queue.put([0,True])
            elif not touch and touch_history["puck_0"]:
                if not self.touch_queue.full():
                    self.touch_queue.put([0,False])
            # sets the touch history of the blue puck to the current touch value
            touch_history["puck_0"] = touch

        # adds True to the yellow puck's touch queue if it wasn't touched before
        # and is now and adds False to the queue if it isn't being touched, but
        # is now. Each value is added with the puck number.
        if puck_number == 1:
            if touch and not touch_history["puck_1"]:
                if not self.touch_queue.full():
                    self.touch_queue.put([1,True])
            elif not touch and touch_history["puck_1"]:
                if not self.touch_queue.full():
                    self.touch_queue.put([1,False])
            # sets the touch history of the yellow puck to the current value
            touch_history["puck_1"] = touch


    def checkForNewPuckData(self):
        '''
        Directs the incoming data the correct parsing functions

        Directs the full input byte array to the PuckPacket parsing functions
        for each puck and for parsing the RX radio data.
        '''
        # if data is being received, divide the data to the right functions
        if self.receiving_data:
            try:
                input = list(self.input)
                # parse the dongle's RX radio data
                self.parse_rx_data(bytearray(input[60:62]))
                # parse the blue puck's data packet
                self.puck_0_packet.parse(bytearray(input[0:30]))
                # parse the yellow puck's data
                self.puck_1_packet.parse(bytearray(input[30:60]))

                # set each puck's touch attribute from the touch queue until
                # its empty
                while not self.touch_queue.empty():
                    puck_number, state = self.touch_queue.get()
                    if puck_number == 0 and state:
                        self.puck_0_packet.touch = state
                    elif puck_number == 1 and state:
                        self.puck_1_packet.touch = state

            except Exception as e:
                if self.print_debug: print(e)
            finally:
                pass


    def parse_rx_data(self, rx_data: bytearray):
        '''
        Extract out the RX radio data from the input stream

        Parameters
        ----------
        rx_data : bytearray
            The radio data part of the input byte array
        '''
        # get the rx_data as an unsigned short
        rx_data = struct.unpack("<H", rx_data)[0]
        # use bit shifts to get each of the radio data values
        self.rx_hardware_state = rx_data >> 13
        self.rx_channel = (rx_data & 0b0001111111000000) >> 6
        self.block_1_pipe = (rx_data & 0b111000) >> 3
        self.block_0_pipe = (rx_data & 0b111)


    def send_command(self, puck_number: int, command: int, message: int,
        last_byte: int):
        '''
        Formats a command to one of the pucks

        Parameters
        ----------
        puck_number : int
            id of the puck. 0 = blue, 1 = yellow
        command : int
            id of what kind of action to take
        message : int
            the action to send
        last_byte : int
            modifier for the action
        '''
        command = (0b11100000 & (puck_number << 5)) | command
        if self.is_plugged():
            pass
            ## put the message in the usb out queue
            if not self.usb_out_queue.full():
                self.usb_out_queue.put([0x00, command, message, last_byte])
                if self.print_debug:
                    print("queued 0x%x , 0x%x to puck %s" % (command,
                        message << 8 | last_byte, puck_number))


    def note_sending(self, output_message: str):
        '''
        Sends a message to the error log

        Parameters
        ----------
        output_message : str
            Message to log into the error report
        '''
        # if the error report path is set, log a message to the error log
        if self.error_report_path:
            with open(os.path.join(self.error_report_path,
                "usb_sending.txt"), 'w') as output_stream:
                output_stream.write("%s"%output_message)


    def actuate(self, puck_number: int, duration: int, amplitude: int,
    action_type: str = "blink", actuator: str = "motor"):
        '''
        Sends a command to "blink" or pulse one of the lights or the motor

        This method turns one of the lights or the motor on for a specified
        duration. It also makes sure that actuation method is not used to often.

        Parameters
        ----------
        puck_number : int
            ID for which puck is sent the actuate command
        duration : int
            The amount of time to actuate the puck
        amplitude : int
            The strength of the actuation
        action_type : string, default = "blink"
            What kind of action to take. Should be "pulse" or "blink"
        actuator : string, default = "motor"
            Which light to actuate or the motor
        '''
        # checks if the puck has been actuated recently
        if puck_number == 0 and ((time.time() - self.last_sent[0]) < 0.2):
            return
        elif puck_number == 1 and ((time.time() - self.last_sent[1]) < 0.2):
            return
        # sets when the puck was actuated last
        self.last_sent[puck_number] = time.time()
        # converts the duration to a byte value
        duration_byte = min(duration*255/1500, 255)
        # saturates the amplitude to 100
        amplitude = min(amplitude, 100)

        # send the formatted actuation command
        try:
            command = COMMANDS.get(actuator).get(action_type)
            self.send_command(puck_number, command, duration_byte, amplitude)
        except Exception as e:
            if self.print_debug: print("in hid_puck, actuate - " + str(e))


    def set_touch_buzz(self, puck_number: int, value: int):
        '''
        Turns the vibration when touched feature on or off

        Parameters
        ----------
        puck_number : int
            ID for which puck is sent the actuate command
        value : int
            message for if the vibration should be on (1) or off (0)
        '''
        self.send_command(puck_number, TOUCHBUZ, 0, value)


    def change_rx_freq(self, new_frequency: int):
        '''
        Changes the frequency of the RX radio

        Parameters
        ----------
        new_frequency : int
            The desired communication frequency of the RX radio
        '''
        self.send_command(0, RXCHANGEFREQ, 0, new_frequency)


    def set_usb_pipes(self, packet_0_pipe: int = 0, packet_1_pipe: int = 1):
        '''
        Tell the dongle which pipes to send over the usb connection

        Parameters
        ----------
        packet_0_pipe : int, default = 0
            pipe for the blue puck's data
        packet_1_pipe : int, default = 1
            pipe for the yellow puck's data
        '''
        packet_0_pipe = min(packet_0_pipe, 5)
        packet_1_pipe = min(packet_1_pipe, 5)
        self.send_command(0, SETUSBPIPES, packet_0_pipe, packet_1_pipe)


    def start_spy(self, channel: int = 12, duration: int = 100):
        '''
        Spy on a particular channel for a specific amount of time

        Parameters
        ----------
        channel : int, default = 12
            Channel to spy on
        duration : int
            a byte for the length of time to spy
        '''
        # note that spy_channel is the channel (0, 127)
        if duration > 255: # limit duration to 255
            duration = 255
        self.send_command(0, CHANSPY, channel, duration)


    def stop(self):
        '''
        Set the is_open value to False
        '''
        self.is_open = False


    def close(self):
        '''
        Reset the puck's to default state and close the input thread
        '''
        # resets the motor buzz on touch feature
        if self.is_plugged() and self.is_open:
            try:
                self.set_touch_buzz(0,1)
                self.set_touch_buzz(1,1)
            except:
                pass

        # sets the open flag to false and terminate the input thread
        self.is_open = False
        if self.input_thread.is_alive():
            self.input_thread.join()
        self.input_thread = threading.Thread(target=self.input_checker)


    def is_opened(self) -> bool:
        '''
        Returns the is_open variable

        Returns
        -------
        bool
            is_open value
        '''
        return self.is_open


    def is_plugged(self) -> bool:
        '''
        Checks if the dongle is in the list of hardware input devices

        Returns
        -------
        bool
            True if the dongle if found
        '''
        for device in hid.enumerate():
            if device['product_id'] == self.PRODUCT_ID and \
               device['vendor_id'] == self.VENDOR_ID:
               return True
        
        return False


    def is_plugged_fast(self) -> bool:
        '''
        Simplified is_plugged method to check if the dongle is receiving data

        Returns
        -------
        bool
            Returns the receiving_data flag
        '''
        return self.receiving_data


    def get_device_info(self) -> hid.device:
        '''
        Finds the hardware input device for the dongle

        Returns
        -------
        hid.device()
            Returns device for the dongle base on the product id and vendor id
        '''
        # for all devices on a computer return device for the dongle if found
        for device in hid.enumerate():
            if device['product_id'] == self.PRODUCT_ID and \
               device['vendor_id'] == self.VENDOR_ID:
               return device


if __name__ == "__main__":
    '''
    Spy on channel 12 and connect to both pucks

    Does a simple check on the function of the dongle
    '''
    print("spy on channel 12")
 
    try:
        puck = HIDPuckDongle()
        puck.open()
        print(puck.is_open)
        puck.start_spy(12, 200)
        for i in range(0, 2500):
            puck.checkForNewPuckData()
            print(puck.rx_channel, puck.puck_0_packet.connected, puck.puck_1_packet.connected)
            time.sleep(0.01)
    except Exception as e:
        print(e)
    finally:
        puck.close()
