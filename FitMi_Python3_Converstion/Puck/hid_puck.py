import hid
import time
import threading
import sys
import struct
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" # suppresses pygame welcome message
import pygame
from Puck.puck_packet import PuckPacket
import queue

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
TOUCHBUZ     = 0x11 # Turn touch buz on and off (1 and 0)
CHANGEFREQ   = 0x12 # Change the frequency of data polling?
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
    '''
    ##---- initialization ----------------------------------------------------##
    def __init__(self, error_report=None):
        '''
        Setup threads and variables for communicating with the pucks

        Setup the threads for communicating with the pucks and the data
        variables that store communication data. Performs the relevant steps to
        set up the dongle as a hardware input device.
        '''
        # set the hardware ids of the dongle
        self.VENDOR_ID = 0x04d8 # do not change this
        self.PRODUCT_ID = 0x2742 # do not change this

        self.print_debug = False

        # NOTE: Do not configure the dongle as a joystick hardware input device
        # (hid). pygame is used to wait in specific threads and will take
        # control of it automatically.
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
        self.block1_pipe = 1

        # setup the input checking thread
        self.input_thread = threading.Thread(target=self.inputChecker)
        self.input = None

        # setup the queues of output data and the log of touches to the puck
        self.usb_out_queue = queue.Queue(maxsize=10)
        self.touch_queue = queue.Queue(maxsize=10)

        # instantiate the last time each puck was touched to 0
        self.last_sent = [0.0, 0.0]

    ##---- open device -------------------------------------------------------##
    def open(self):
        if not self.is_plugged():
            return

        ## if we are open, close first then re-open.
        if self.print_debug: print("dongle open?")
        try:
            self.dongle.close()
        except:
            pass

        self.dongle.open(self.VENDOR_ID, self.PRODUCT_ID)
        if self.print_debug: print("manufacturer: %s" % self.dongle.get_manufacturer_string())
        if self.print_debug: print("product: %s" % self.dongle.get_product_string())

        self.is_open = True
        self.input_thread.start()

        self.plug_state = True
        self.receiving_data = False
        self.check_connection()
        self.wait_for_data()

        #pygame.time.wait(10) # give thread time to start
        self.sendCommand(0,GAMEON, 0x00, 0x01) # puts puck 0 into game mode
        self.sendCommand(1,GAMEON, 0x00, 0x01) # puts puck 1 into game mode


    ##---- check if we are getting data from either puck. if not, reset the
    ## RX radio and wait for it to startup
    def check_connection(self):
        radio_working = False
        for i in range(0, 200):
            self.checkForNewPuckData()
            if self.puck_0_packet.connected or self.puck_1_packet.connected:
                radio_working = True
                break
            pygame.time.wait(1)
        self.sendCommand(0,DNGLRST, 0x00, 0x00)
        pygame.time.wait(600)  # wait until we are getting data

    ##---- wait till receiving data ------------------------------------------##
    def wait_for_data(self):
        for i in range(0, 200):
            pygame.time.wait(1)  # wait until we are getting data
            if self.receiving_data:
                break

    ##---- input checker -----------------------------------------------------##
    ## checks whether the input value has changed.
    def inputChecker(self):
        readFailCount = 0
        tooManyFails = 70
        tick = 0

        touch_history = {"puck0": False, "puck1": False}
        while self.is_open:
            try:
                self.input = self.dongle.read(62)
                if not self.input:
                    readFailCount += 1
                    if readFailCount > tooManyFails:
                        self.receiving_data = False
                else:
                    readFailCount = 0
                    self.receiving_data = True
                    ## quickly catch touch events.
                    self.check_for_touch(self.input, touch_history, puck_number=0)
                    self.check_for_touch(self.input, touch_history, puck_number=1)

                if not self.usb_out_queue.empty():
                    self.dongle.write(self.usb_out_queue.get()) # first byte is report id
                    
            except Exception as e:
                self.receiving_data = False
                if self.print_debug: print(e)
            finally:
                time.sleep(0.00001)
                
        # Make sure we clear the queue
        for i in range(10):
            if not self.usb_out_queue.empty():
                self.dongle.write(self.usb_out_queue.get()) # first byte is report id
            else:
                break
        self.dongle.close()

    ##---- parse the status byte to determine if there was a touch event -----##
    ## Touch event can be too fast for the game loop to catch them. Missing
    ## touch events can make the game feel broken. This thread runs faster than
    ## the game loop and makes it more likely that we will catch touch events
    ## that the game loop might have missed.
    def check_for_touch(self, input, touch_history, puck_number=0):
        index = 29
        if puck_number == 1:
            index = 59

        status = input[index]
        touch = (status & 0b00000100) >> 2

        if puck_number == 0:
            if touch and not touch_history["puck0"]:
                if not self.touch_queue.full():
                    self.touch_queue.put([0,True]) ## put in the puck number
            elif not touch and touch_history["puck0"]:
                if not self.touch_queue.full():
                    self.touch_queue.put([0,False]) ## put in the puck number
            touch_history["puck0"] = touch

        if puck_number == 1:
            if touch and not touch_history["puck1"]:
                if not self.touch_queue.full():
                    self.touch_queue.put([1,True]) ## put in the puck number
            elif not touch and touch_history["puck1"]:
                if not self.touch_queue.full():
                    self.touch_queue.put([1,False]) ## put in the puck number
            touch_history["puck1"] = touch

    ##---- run this method in game loop to parse incoming data.
    def checkForNewPuckData(self):
        if self.receiving_data:
            try:
                input = list(self.input)
                self.parse_rxdata(bytearray(input[60:62]))
                self.puck_0_packet.parse(bytearray(input[0:30]))
                self.puck_1_packet.parse(bytearray(input[30:60]))

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

    ##----
    def parse_rxdata(self, rxdata):
        rxdata = struct.unpack("<H", rxdata)[0]
        self.rx_hardware_state = rxdata >> 13
        self.rx_channel = (rxdata & 0b0001111111000000) >> 6
        self.block1_pipe = (rxdata & 0b111000) >> 3
        self.block_0_pipe = (rxdata & 0b111)

    ##---- send a command to the pucks ---------------------------------------##
    def sendCommand(self, puck_number, cmd, msb, lsb):
        command = (0b11100000 & (puck_number << 5)) | cmd
        if self.is_plugged():
            pass
            ## put our message in the usb out queue
            if not self.usb_out_queue.full():
                self.usb_out_queue.put([0x00, command, msb, lsb])
                if self.print_debug: print("queued 0x%x , 0x%x to puck %s" % (cmd, msb << 8 | lsb, puck_number))

    def note_sending(self, value):
        # if the error report path is set
        if self.error_report_path:
            with open(os.path.join(self.error_report_path, "usb_sending.txt"), 'w') as f:
                f.write("%s"%value)

    ##---- buzz motor --------------------------------------------------------##
    def actuate(self, puck_number, duration, amp, action_type="blink", actuator="motor"):
        ## do not spam the pucks with actuator commands
        if puck_number == 0 and ((time.time() - self.last_sent[0]) < 0.2):
            return
        elif puck_number == 1 and ((time.time() - self.last_sent[1]) < 0.2):
            return
        self.last_sent[puck_number] = time.time()
        duration_byte = min(duration*255/1500, 255)
        amp = min(amp, 100)
        try:
            cmd = COMMANDS.get(actuator).get(action_type)
            self.sendCommand(puck_number, cmd, duration_byte, amp)
        except Exception as e:
            if self.print_debug: print("in hid_puck, actuate - " + str(e))

    ##---- set touch buzz ----------------------------------------------------##
    def setTouchBuzz(self, puck_number, value):
        self.sendCommand(puck_number, TOUCHBUZ, 0, value)

    ##---- change RX frequency -----------------------------------------------##
    def changeRXFreq(self, new_frequency ):
        self.sendCommand(0, RXCHANGEFREQ, 0, new_frequency)

    ##---- tell the receiver which pipes to send over the usb connection -----##
    def setUSBPipes(self, pack0_pipe=0, pack1_pipe=1):
        pack0_pipe = min(pack0_pipe, 5)
        pack1_pipe = min(pack1_pipe, 5)
        self.sendCommand(0, SETUSBPIPES, pack0_pipe, pack1_pipe)

    ##---- spy on a particular channel for a limited amount of time ---------##
    def startSpy(self, spy_channel=12, duration=100):
        # note that spy_channel is  the channel (0, 127)
        if duration > 255:
            duration = 255
        self.sendCommand(0, CHANSPY, spy_channel, duration)

    ##---- thread start ------------------------------------------------------##
    def stop(self):
        self.is_open = False

    ##---- thread start ------------------------------------------------------##
    def close(self):
        if self.is_plugged() and self.is_open:
            try:
                self.setTouchBuzz(0,1)
                self.setTouchBuzz(1,1)
            except:
                pass
        self.is_open = False
        if self.input_thread.is_alive():
            self.input_thread.join()
        self.input_thread = threading.Thread(target=self.inputChecker)

    ##---- is connected ------------------------------------------------------##
    def is_opened(self):
        return self.is_open

    ##---- check connection --------------------------------------------------##
    def is_plugged(self):
        for device in hid.enumerate():
            if device['product_id'] == self.PRODUCT_ID and \
               device['vendor_id'] == self.VENDOR_ID:
               return True

    ##---- infrequently check if the device is plugged in --------------------##
    def is_plugged_fast(self):
        # return the value from our thread
        return self.receiving_data

    ##---- get the information about the device ------------------------------##
    def getDeviceInfo(self):
        for device in hid.enumerate():
            if device['product_id'] == self.PRODUCT_ID and \
               device['vendor_id'] == self.VENDOR_ID:
               return device

if __name__ == "__main__":
    print("spy on channel 12")
    import time
    import os
    try:
        pk = HIDPuckDongle()
        pk.open()
        print(pk.is_open)
        pk.startSpy(12, 200)
        for i in range(0, 2500):
            pk.checkForNewPuckData()
            print(pk.rx_channel, pk.puck_0_packet.connected, pk.puck_1_packet.connected)
            time.sleep(0.01)
    except Exception as e:
        print(e)
    finally:
        pk.close()
