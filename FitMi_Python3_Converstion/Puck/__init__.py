'''
A library to connect to each of the FitMi pucks, poll their data and process it.

This library has code to connect the dongle for the FitMi pucks and poll data from their accelerometers, gyroscope, magnetometer, and load cell. Data also available is the linear velocity and quaternion representing the rotation of each puck, the battery, and status of the pucks among other variables and helper functions for analyzing the data.

Modules
-------
hid_puck
    The definition for the HIDPuckDongle class. It controls all of the communication to and from the dongle for the FitMi pucks
puck_packet
    The definition for the PuckPacket class. It parses and contains the data from the pucks for the accelerometer, gyroscope, magnetometer, velocity measurement, quaternion, roll, pitch, and yaw angles; load cell, battery, charging indicator, connection indicator, touch status, status for the IMU, status for if the velocity is polled, the state, and a variable called res_v5
puck_task
    Class definition of PuckTask. Analyzes a single degree of freedom and changes a state variable when the degree of freedom of the puck moves above and below a specific angle range.
quaternion
    Helper functions for working with quaternions
scan_packet
    The definition of the ScanPacket class. It characterizes the pipe channels of the scan.
'''