import struct

class ScanPacket(object):
    '''
    Helper functions for analyzing the scan data packet

    Analyzes which channels were found, how many were found, and what the scanning channel was.

    Attributes
    ----------
    pipe_channels : List[int]
        A list of six pipe channels for data
    pipe_found_count : List[int]
        A list of six counter variables to indicate if each pipe channel was found
    scan_channel : int
        The channel the data was scanned on
    battery : int
        The battery percentage of the puck
    status : int
        The status of the puck
    packet_def : string
        A string used to parse the data stream for the pipe channels, found channels, scanning time, battery percentage, and status
    
    Methods
    -------
    __init__()
        Initializes the packet of received scan data to default values
    create_packet_definition
        Creates the string for parsing the scan data stream
    parse(raw_data)
        Uses the packet definition to parse the scan data.
    __str__()
        Prints the pipe channels, the number of channels, and the scan channel
    '''
    def __init__(self):
        '''
        Initializes the packet of received scan data to default values
        '''
        self.pipe_channels = [-1, -1, -1, -1, -1, -1]
        self.pipe_found_count = [-1, -1, -1, -1, -1, -1]
        self.scan_channel = -1
        self.battery = -1
        self.status = -1
        self.packet_def = self.create_packet_definition()

    def create_packet_definition(self):
        '''
        Creates the string for parsing the scan data stream

        Returns
        -------
        string
            The combined format string for parsing the incoming byte data in the scan packet
        '''
        pipe_channel = "hhhhhh"
        found_count  = "hhhhhh"
        scan_time = "h"
        battery  = "B"
        status   = "B"
        return "<"+pipe_channel+found_count+scan_time+battery+status

    def parse(self, raw_data):
        '''
        Uses the packet definition to parse the scan data.

        Scan data is parsed into the found pipe channels, the count of the pipe channels found, the scan channel, battery percentage, and status.

        Parameters
        ----------
        raw_data : bytearray
            The incoming data from scanning
        '''
        data = struct.unpack(self.packet_def, raw_data)
        self.pipe_channels = list(data[0:6])
        self.pipe_found_count = list(data[6:12])
        self.scan_channel = data[12]
        self.battery = data[13]
        self.status = data[14]

    def __str__(self):
        '''
        Prints the pipe channels, the number of channels, and the scan channel

        When the ScanPacket object is printed, it prints the pipe channels, how many were found, and the scan channel.
        '''
        number_found = sum([n for n in self.pipe_found_count if n > 0])
        f = self.pipe_channels + [number_found] + [self.scan_channel]
        return str(f)#"channels: p0 %s, p1 %s, p2 %s, p3 %s, p4 %s, p5 %s, number_found: %s, scan_channel: %s" % f
