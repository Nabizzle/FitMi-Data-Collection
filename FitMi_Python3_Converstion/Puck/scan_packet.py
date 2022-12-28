##----------------------------------------------------------------------------##
##---- RX scan data packet ---------------------------------------------------##
##----------------------------------------------------------------------------##

import struct

##---- Scan Packet -----------------------------------------------------------##
class ScanPacket(object):
    def __init__(self):
        self.pipe_channels = [-1, -1, -1, -1, -1, -1]
        self.pipe_found_count = [-1, -1, -1, -1, -1, -1]
        self.scan_channel = 0 # not implemented
        self.packet_def = self.create_package_definition()

    ##---- Define the structure of the packet --------------------------------##
    def create_package_definition(self):
        # note: I'm combining them this way for readability - this could just be one string
        pipe_channel = "hhhhhh"
        found_count  = "hhhhhhh"
        scan_time = "h"
        battery  = "B"
        status   = "B"
        return "<"+pipe_channel+found_count+scan_time+battery+status

    ##---- parse a data packet -----------------------------------------------##
    def parse(self, raw_data):
        data = struct.unpack(self.packet_def, raw_data)
        self.pipe_channels = list(data[0:6])
        self.pipe_found_count = list(data[6:12])
        self.scan_channel = data[13]

    def __str__(self):
        number_found = sum([n for n in self.pipe_found_count if n > 0])
        f = self.pipe_channels + [number_found] + [self.scan_channel]
        return str(f)#"channels: p0 %s, p1 %s, p2 %s, p3 %s, p4 %s, p5 %s, number_found: %s, scan_channel: %s" % f
