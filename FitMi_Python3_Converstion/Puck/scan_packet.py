##----------------------------------------------------------------------------##
##---- RX scan data packet ---------------------------------------------------##
##----------------------------------------------------------------------------##

import struct

##---- Scan Packet -----------------------------------------------------------##
class ScanPacket(object):
    def __init__(self):
        self.pipe_channels = [-1, -1, -1, -1, -1, -1]
        self.pipe_found_count = [-1, -1, -1, -1, -1, -1]
        self.scanchan = 0 # not implemented
        self.packet_def = self.create_package_definition()

    ##---- Define the structure of the packet --------------------------------##
    def create_package_definition(self):
        # note: I'm combining them this way for readability - this could just be one string
        pipechan = "hhhhhh"
        foundcount  = "hhhhhhh"
        scantime = "h"
        battery  = "B"
        status   = "B"
        return "<"+pipechan+foundcount+scantime+battery+status

    ##---- parse a data packet -----------------------------------------------##
    def parse(self, raw_data):
        data = struct.unpack(self.packet_def, raw_data)
        self.pipe_channels = list(data[0:6])
        self.pipe_found_count = list(data[6:12])
        self.scanchan = data[13]

    def __str__(self):
        nfound = sum([n for n in self.pipe_found_count if n > 0])
        f = self.pipe_channels + [nfound] + [self.scanchan]
        return str(f)#"channels: p0 %s, p1 %s, p2 %s, p3 %s, p4 %s, p5 %s, nfound: %s, scanchan: %s" % f
