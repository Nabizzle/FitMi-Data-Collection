##----------------------------------------------------------------------------##
##---------------- Rehab puck hid interface ----------------------------------##
##----------------------------------------------------------------------------##
## note that the puck must not be configured as a joystick. pygame automatically
## tries to take control of joysticks and that prevents us from handling the
## device ourselves.

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

# command definitions
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
    ##---- initialization ----------------------------------------------------##
    def __init__(self, err_rpt=None, operating_system="Windows"):
        self.idVendor = 0x04d8 # do not change this
        self.idProduct = 0x2742 # do not change this
        self.release = 0
        self.verbosity = 0
        self.dongle = hid.device()
        self.inputPrev = None
        self.isopen = False

        if err_rpt is not None:
            self.err_rpt_path = err_rpt
            if not os.path.exists(self.err_rpt_path):
                os.makedirs(self.err_rpt_path)
        else:
            self.err_rpt_path = None

        ## packet definitions specifies the structure of the packet.
        self.receivingData = False
        self.puck_0_packet = PuckPacket()
        self.puck_1_packet = PuckPacket()
        self.rx_hardware_state = 0;
        self.rx_channel = 0;
        self.block0_pipe = 0;
        self.block1_pipe = 1;

        self.iThread = threading.Thread(target=self.inputChecker)
        self.lock = threading.Lock()
        self.input = None
        self.input_count = 0
        self.callback = lambda input: sys.stdout.write(str(input) + "\n")
        self.emptyDataCount = 0
        self.plugState = False

        self.usb_out_queue = queue.Queue(maxsize=10)
        self.touch_queue = queue.Queue(maxsize=10)

        self.last_sent = [0,0]

        self.my_os = operating_system

    ##---- open device -------------------------------------------------------##
    def open(self):
        if not self.is_plugged():
            return

        ## if we are open, close first then re-open.
        if self.verbosity > 0: print("dongle open?")
        try:
            self.dongle.close()
        except:
            pass

        self.dongle.open(self.idVendor, self.idProduct)
        if self.verbosity > 0: print("manufacturer: %s" % self.dongle.get_manufacturer_string())
        if self.verbosity > 0: print("product: %s" % self.dongle.get_product_string())

        self.isopen = True
        self.iThread.start()

        self.plugState = True
        self.emptyDataCount = 0
        self.receivingData = False
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
            if self.receivingData:
                break

    ##---- set input change callback -----------------------------------------##
    def setCallback(self, callback):
        self.callback = callback

    ##---- input checker -----------------------------------------------------##
    ## checks whether the input value has changed.
    def inputChecker(self):
        readFailCount = 0
        tooManyFails = 70
        tick = 0

        touch_history = {"puck0": False, "puck1": False}
        while self.isopen:
            try:
                self.input = self.dongle.read(62)
                if not self.input:
                    readFailCount += 1;
                    if readFailCount > tooManyFails:
                        self.receivingData = False
                else:
                    readFailCount = 0
                    self.receivingData = True
                    ## quickly catch touch events.
                    self.check_for_touch(self.input, touch_history, puck_number=0)
                    self.check_for_touch(self.input, touch_history, puck_number=1)

                if not self.usb_out_queue.empty():
                    self.dongle.write(self.usb_out_queue.get()) # first byte is report id
                    
            except Exception as e:
                self.receivingData = False
                if self.verbosity > 1: print(e)
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
        if self.receivingData:
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
                if self.verbosity > 0: print(e)
            finally:
                pass

    ##----
    def parse_rxdata(self, rxdata):
        rxdata = struct.unpack("<H", rxdata)[0]
        self.rx_hardware_state = rxdata >> 13;
        self.rx_channel = (rxdata & 0b0001111111000000) >> 6;
        self.block1_pipe = (rxdata & 0b111000) >> 3
        self.block0_pipe = (rxdata & 0b111)

    ##---- send a command to the pucks ---------------------------------------##
    def sendCommand(self, puck_number, cmd, msb, lsb):
        command = (0b11100000 & (puck_number << 5)) | cmd
        if self.is_plugged():
            pass
            ## put our message in the usb out queue
            if not self.usb_out_queue.full():
                self.usb_out_queue.put([0x00, command, msb, lsb])
                if self.verbosity > 0: print("queued 0x%x , 0x%x to puck %s" % (cmd, msb << 8 | lsb, puck_number))


    def note_sending(self, value):
        if self.err_rpt_path:
            with open(os.path.join(self.err_rpt_path, "usb_sending.txt"), 'w') as f:
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
            if self.verbosity > 0: print("in hid_puck, actuate - " + str(e))

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
        self.isopen = False

    ##---- thread start ------------------------------------------------------##
    def close(self):
        if self.is_plugged() and self.isopen:
            try:
                self.setTouchBuzz(0,1)
                self.setTouchBuzz(1,1)
            except:
                pass
        self.isopen = False
        if self.iThread.is_alive():
            self.iThread.join()
        self.iThread = threading.Thread(target=self.inputChecker)

    ##---- is connected ------------------------------------------------------##
    def is_opened(self):
        return self.isopen

    ##---- check connection --------------------------------------------------##
    def is_plugged(self):
        for device in hid.enumerate():
            if device['product_id'] == self.idProduct and \
               device['vendor_id'] == self.idVendor:
               return True

    ##---- infrequently check if the device is plugged in --------------------##
    def is_plugged_fast(self):
        # return the value from our thread
        return self.receivingData

    ##---- get the information about the device ------------------------------##
    def getDeviceInfo(self):
        for device in hid.enumerate():
            if device['product_id'] == self.idProduct and \
               device['vendor_id'] == self.idVendor:
               return device

if __name__ == "__main__":
    print("spy on channel 12")
    import time
    import os
    try:
        pk = HIDPuckDongle()
        pk.open()
        print(pk.isopen)
        pk.startSpy(12, 200)
        for i in range(0, 2500):
            pk.checkForNewPuckData()
            print(pk.rx_channel, pk.puck_0_packet.connected, pk.puck_1_packet.connected)
            time.sleep(0.01)
    except Exception as e:
        print(e)
    finally:
        pk.close()
