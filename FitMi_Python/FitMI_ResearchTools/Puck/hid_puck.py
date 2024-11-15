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
import pygame
from puck_packet import PuckPacket
import numpy as np
import os
import Queue

RBLINK     = 0x01
GBLINK     = 0x02
BBLINK     = 0x03
RPULSE     = 0x05
MBLINK     = 0x04
GPULSE     = 0x06
BPULSE     = 0x07
MPULSE     = 0x08
MPUENBL    = 0x09
PWR        = 0x0A
GAMEON     = 0x0B
MAGCALX    = 0x0C    ## send mag cal data back to puck
MAGCALY    = 0x0D    ## send mag cal data back to puck
MAGCALZ    = 0x0E    ## send mag cal data back to puck
DNGLRST    = 0x0F    ## reset the dongle
SENDVEL    = 0x10    ## send velocity (data==1) or send magnetometer (data==0)
TOUCHBUZ   = 0x11    ## turn touch buz on and off (1 and 0)
CHANGEFREQ = 0x12
RXCHANGEFREQ = 0x13
CHANSPY      = 0x14
SETUSBPIPES  = 0x15

COMMANDS = {"red": {"blink": RBLINK, "pulse": RPULSE},
            "green": {"blink": GBLINK, "pulse": GPULSE},
            "blue": {"blink": BBLINK, "pulse": BPULSE},
            "motor": {"blink": MBLINK, "pulse": MPULSE}}

class HIDPuckDongle(object):
    ##---- initizilzation ----------------------------------------------------##
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
        self.puckpack0 = PuckPacket()
        self.puckpack1 = PuckPacket()
        self.rx_hardware_state = 0;
        self.rx_channel = 0;
        self.block0_pipe = 0;
        self.block1_pipe = 1;

        self.iThread = threading.Thread(target=self.inputChecker)
        self.lock = threading.Lock()
        self.inpt = None
        self.inptCount = 0
        self.callback = lambda inpt, inpt2 : sys.stdout.write(str(inpt) + "\n")
        self.emptyDataCount = 0
        self.plugState = False

        self.usb_out_queue = Queue.Queue(maxsize=10)
        self.touch_queue = Queue.Queue(maxsize=10)

        self.last_sent = [0,0]

        self.myos = operating_system

    ##---- open device -------------------------------------------------------##
    def open(self):
        if not self.is_plugged():
            return

        ## if we are open, close first then re-open.
        if self.verbosity > 0: print "dongle open?"
        try:
            self.dongle.close()
        except:
            pass

        self.dongle.open(self.idVendor, self.idProduct)
        if self.verbosity > 0: print "manufacturer: %s" % self.dongle.get_manufacturer_string()
        if self.verbosity > 0: print "product: %s" % self.dongle.get_product_string()

        self.isopen = True
        self.iThread.start()

        self.plugState = True
        self.emptyDataCount = 0
        #self.wait_for_data() # give thread time to start
        #self.sendCommand(0,DNGLRST, 0x00, 0x00)  # pipe and data are irelevant
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
            if self.puckpack0.connected or self.puckpack1.connected:
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
            #self.lock.acquire()
            try:
                #self.inptCount += 1
                self.inpt = self.dongle.read(62)
                if not self.inpt:
                    readFailCount += 1;
                    if readFailCount > tooManyFails:
                        self.receivingData = False
                else:
                    readFailCount = 0
                    self.receivingData = True
                    ## quickly catch touch events.
                    self.check_for_touch(self.inpt, touch_history, pucknum=0)
                    self.check_for_touch(self.inpt, touch_history, pucknum=1)

                if not self.usb_out_queue.empty():
                    # self.dongle.set_nonblocking(1)
                    # if self.verbosity < 0: print "Trying to write"
                    #self.note_sending(1)
                    self.dongle.write(self.usb_out_queue.get()) # first byte is report id
                    #self.note_sending(0)
                    # if self.verbosity < 0: print "wrote!"
                    # self.dongle.set_nonblocking(0)
                    # pygame.time.wait(1)
                    # self.note_sending(0)
            except Exception as e:
                self.receivingData = False
                if self.verbosity > 1: print e
            finally:
                time.sleep(0.00001)
                #self.lock.release()
            #time.sleep(0.00001)
            #pygame.time.wait(3)  # wait until we are getting data
            #time.sleep(0.003)
            #self.puckpack0.parse(bytearray(inpt[0:30]))
            #self.puckpack1.parse(bytearray(inpt[30:60]))
            #print self.puckpack1
            #print inpt
            #self.callback(self.puckpack0, self.puckpack1)
            #pygame.time.wait(3)

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
    def check_for_touch(self, inpt, touch_history, pucknum=0):
        index = 29
        if pucknum == 1:
            index = 59

        status = inpt[index]#struct.unpack("<B", inpt[index]) ## unpack last byte into uint
        touch = (status & 0b00000100) >> 2

        if pucknum == 0:
            if touch and not touch_history["puck0"]:
                if not self.touch_queue.full():
                    self.touch_queue.put([0,True]) ## put in the puck number
            elif not touch and touch_history["puck0"]:
                if not self.touch_queue.full():
                    self.touch_queue.put([0,False]) ## put in the puck number
            touch_history["puck0"] = touch

        if pucknum == 1:
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
                #print self.puckpack1.connected
                #self.inptCount -= 1
                #self.lock.acquire()
                inpt = list(self.inpt)
                self.parse_rxdata(bytearray(inpt[60:62]))
                self.puckpack0.parse(bytearray(inpt[0:30]))
                self.puckpack1.parse(bytearray(inpt[30:60]))

                while not self.touch_queue.empty():
                    pucknum, state = self.touch_queue.get()
                    if pucknum == 0 and state:
                        self.puckpack0.touch = state
                    elif pucknum == 1 and state:
                        self.puckpack1.touch = state


            except Exception as e:
                if self.verbosity > 0: print e
            finally:
                pass
                #self.lock.release()

    ##----
    def parse_rxdata(self, rxdata):
        rxdata = struct.unpack("<H", rxdata)[0]
        self.rx_hardware_state = rxdata >> 13;
        self.rx_channel = (rxdata & 0b0001111111000000) >> 6;
        self.block1_pipe = (rxdata & 0b111000) >> 3
        self.block0_pipe = (rxdata & 0b111)

    ##---- send a command to the pucks ---------------------------------------##
    def sendCommand(self, pucknum, cmd, msb, lsb):
        command = (0b11100000 & (pucknum << 5)) | cmd
        #for i in range(0, 6):
        if self.is_plugged():
            pass
            # self.note_sending(1)
            ## put our message in the usb out queue
            if not self.usb_out_queue.full():
                self.usb_out_queue.put([0x00, command, msb, lsb])
                if self.verbosity > 0: print "queued 0x%x , 0x%x to puck %s" % (cmd, msb << 8 | lsb, pucknum)
            # self.dongle.set_nonblocking(1)
            # if self.verbosity < 0: print "Trying to write"
            # self.dongle.write() # first byte is report id
            # if self.verbosity < 0: print "wrote!"
            # self.dongle.set_nonblocking(0)
            # pygame.time.wait(1)
            # self.note_sending(0)


    def note_sending(self, value):
        if self.err_rpt_path:
            with open(os.path.join(self.err_rpt_path, "usb_sending.txt"), 'w') as f:
                f.write("%s"%value)

    ##---- buzz motor --------------------------------------------------------##
    def actuate(self, pucknum, duration, amp, atype="blink", actuator="motor"):
        ## do not spam the pucks with actuator commands
        if pucknum == 0 and ((time.time() - self.last_sent[0]) < 0.2):
            return
        elif pucknum == 1 and ((time.time() - self.last_sent[1]) < 0.2):
            return
        self.last_sent[pucknum] = time.time()
        durbyte = min(duration*255/1500, 255)
        amp = min(amp, 100)
        try:
            cmd = COMMANDS.get(actuator).get(atype)
            self.sendCommand(pucknum, cmd, durbyte, amp)
        except Exception as e:
            if self.verbosity > 0: print "in hid_puck, actuate - " + str(e)

    ##---- set touch buzz ----------------------------------------------------##
    def setTouchBuzz(self, pucknum, value):
        self.sendCommand(pucknum, TOUCHBUZ, 0, value)

    ##---- change RX frequency -----------------------------------------------##
    def changeRXFreq(self, newfreq ):
        self.sendCommand(0, RXCHANGEFREQ, 0, newfreq)

    ##---- tell the receiver which pipes to send over the usb connection -----##
    def setUSBPipes(self, pack0_pipe=0, pack1_pipe=1):
        pack0_pipe = min(pack0_pipe, 5)
        pack1_pipe = min(pack1_pipe, 5)
        self.sendCommand(0, SETUSBPIPES, pack0_pipe, pack1_pipe)

    ##---- spy on a particular channel for a limmited amount of time ---------##
    def startSpy(self, spychan=12, duration=100):
        # note that spychan is  the channel (0, 127)
        #duration is in TENS of milliseconds. (0, 255)
        if duration > 255:
            duration = 255
        self.sendCommand(0, CHANSPY, spychan, duration)

    ##---- thread start ------------------------------------------------------##
    def stop(self):
        self.isopen = False

    ##---- thread start ------------------------------------------------------##
    def close(self):
        if self.is_plugged() and self.isopen:
            try:
                #self.sendCommand(0,GAMEON, 0x00, 0x00) ## puts puck 0 into standby
                #self.sendCommand(1,GAMEON, 0x00, 0x00) ## puts puck 1 into standby
                self.setTouchBuzz(0,1)
                self.setTouchBuzz(1,1)
                #self.sendCommand(0,FLUSHBUF, 0x00, 0x00)  # pipe and data are irelevant
                #pygame.time.wait(20)
                #self.dongle.close()
            except:
                pass
        self.isopen = False
        if self.iThread.isAlive():
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
            # else:
            #    print device['product_id'], device['vendor_id']

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
    print "spy on channel 12"
    import time
    import os
    try:
        pk = HIDPuckDongle()
        pk.open()
        print pk.isopen
        pk.startSpy(12, 200)
        for i in range(0, 2500):
            pk.checkForNewPuckData()
            print pk.rx_channel, pk.puckpack0.connected, pk.puckpack1.connected
            time.sleep(0.01)
    except Exception as e:
        print e
    finally:
        pk.close()
