# FitMi-Data-Collection
Code For using the Flint Rehab FitMi pucks for grasp research. The code available is written in Python (2.7 and 3.10), C# (Windows and Xamarin Framework for Android).
The Python 2.7 version was written originally by the Flint Rehab company and the Python 3 version was written by [Nabeel](#authors) by converting the 2.7 code.
[David Pruitt](#author) from UTDallas wrote both C# libraries and graciously sent it to our group for use.

**This Read Me focuses on the usage of the Python 3 code.**

The FitMi pucks consist of a dongle and a blue and yellow puck. The blue puck is considered the first puck in the code and the yellow is the second. The pucks output angular
acceleration, gyroscope angles, linear acceleration, load cell, and quaternion data. The quaternion data is also converted to the roll, pitch, and yaw angles of the puck in the code.

> **Warning**
>
> **Do not use the Python 2.7 version of the code. In the conversion of to Python 3, I found many bugs that I fixed in the conversion that are still present in the
> python 2.7 version. The android and C# versions will likely work as intended, though I have not tested them at at this time.**

## Hardware Description
The FitMi pucks consist of a blue and yellow puck with a usb dongle for communication:
![FitMi Puck Station](https://github.com/CaseFNI/FitMi-Data-Collection/blob/main/Media/FitMi%20Pucks.png)

The pucks are usually used if a program called Rehab Studio, but we were provided code from [David Pruitt](#authors) from his work with the pucks that allows us direct
access to each pucks rotational accelerometer, gyroscope, linear acceleration measurement, quaternion measurement, and load cell.

> **Note**
> The load cell does not have units with its output to my knowledge

When connecting the the pucks, make sure to take the pucks out of the station and then plug in the dongle. The pucks will flash a purple light and vibrate to tell you
they connected to the dongle. If this does not happen put the dongle back into the station with the pucks and pres the button by the power plug once. Make sure the
station is also connected to the charger. When this happens, the pucks and dongle should flash their lights together.

> **Note**
> The pucks must be removed first from the station before the dongle is plugged in because they do not connect to the dongle if they are also charging. If the charger
is not plugged in, you can connect to them in the station.

### Debugging the Puck Output

If you want to visualize the output of the pucks, you can use two different functions. The [puck_plot.py](#puck_plotpy) script shows the output of the all sensors
of the pucks in a series of subplots. The [show_orientation.py](#show_orientationpy) script shows one of the puck's rotations on a 3D figure. To pick the puck you need
to change the puck number in the script. 0 is the blue puck and 1 is the yellow puck.

## Python Libraries Needed

[Python 3.10.0 or later](https://www.python.org/)
- [Cython version: 0.29.32](https://pypi.org/project/Cython/)
- [hidapi version: 0.12.0.post2](https://pypi.org/project/hidapi/)
- [matplotlib version: 3.6.2](https://pypi.org/project/matplotlib/)
- [numpy version: 1.23.4](https://pypi.org/project/numpy/)
- [pygame 2.1.2](https://pypi.org/project/pygame/)
- [scipy version: 1.9.3](https://pypi.org/project/scipy/)
- [customtkinter version: 5.0.3](https://pypi.org/project/customtkinter/0.3/)
- [seaborn version: 0.12.2](https://pypi.org/project/seaborn/)

## Testing electronics

* [FlintRehab FitMi Pucks](https://www.flintrehab.com/product/fitmi/)

## Running the tests

Take the pucks out of the station and then connect the dongle. If the pucks connect, they will flash a purple light and vibrate. To run a script, type python followed
by the script's name in the console.

## What is a Quaternion and What is it Used For?

Quaternions are a four dimensional number system similar to the imaginary number system. While the imaginary numbers represent a point in 2D as $x+yi$ where x is a point along the x or real number axis and y is a point along the y or imaginary number axis, quaternions represent a 4D point as $q=w+xi+yj+zk$ where all four axes are orthogonal to each other.

Using quaternions is mostly used today as a way to represent the rotation of a point without the drawbacks of using Euler angles like [[Gimbal Lock]] and discontinuities. Using quaternions to rotate a point is also much more compact than using a rotation matrix.

When using a quaternion to rotate a point, we use a unit quaternion where $||q|| = \sqrt{w^2 + x^2 + y^2 + z^2} = 1$. We also take advantage of the fact that a quaternion can be written as $q = \cos{\left(\frac{\theta}{2} \right)} + \sin{\left(\frac{\theta}{2} \right)}(xi+yj+zk)$  where $\theta$ is the angle we want to rotate by and $[x, y, z]$ forms the unit vector for the axis of rotation . In this format, a point $p$ rotated $\theta$ degrees/radians is done by:

$p' = qpq^{-1}$

Where $p$ is a point converted to a **pure quaternion**: $p = 0 + p_x i + p_y j + p_z k$ and $q^{-1}$ is the conjugate of $q$ where $q^{-1} = \cos{\left(\frac{\theta}{2} \right)} - \sin{\left(\frac{\theta}{2} \right)}(xi+yj+zk)$
> **Note**
> - The angle is $\frac{\theta}{2}$ because the first quaternion rotates the point half way and the second rotates it the other way.
> - Multiplication of quaternions is not commutative. Left multiplying is a rotation following the right hand rule. Right multiplying is the left hand rule.
> > **Note**
> > - The angle in the conjugate is negative, but has been made positive here as per a cosine identity

| $row \times column$  | **$\boldsymbol{1}$** | **$\boldsymbol{i}$** | **$\boldsymbol{j}$** | **$\boldsymbol{k}$** |
| -------------------- | -------------------- | -------------------- | -------------------- | -------------------- |
| **$\boldsymbol{1}$** | $1$                  | $i$                  | $j$                  | $k$                  |
| **$\boldsymbol{i}$** | $i$                  | $-1$                 | $k$                  | $-j$                 |
| **$\boldsymbol{j}$** | $j$                  | $-k$                 | $-1$                 | $i$                  |
| **$\boldsymbol{k}$** | $k$                  | $j$                  | $-i$                 | $-1$                 |

Quaternions can also be converted to Rotation Matrices by following a specific formula for conversion.

## Authors

- [**FlintRehab**](https://www.flintrehab.com/) - Creator of the original Python 2.7 version of the code
- [**David Pruitt**](https://www.researchgate.net/profile/David-Pruitt) - Creator of the C# versions of the code and the person who shared the code with me.
- **Nabeel Chowdhury** - Converted the Python 2.7 code to Python 3.10 and cleaned and documented the code.

## Acknowledgements

- [FlintRehab](https://www.flintrehab.com/) - Created the pucks and made the original code
- [Seth Hays Lab](https://research.utdallas.edu/blog/dr-seth-hays-neuroplasticity-and-the-wandering-nerve) - Provided access to the code to the Tyler Lab

# Description of Each Script

## Main Scripts

### plot_puck_data_gui.py

Shows the output of the two pucks in the same way that [puck_plot.py](#puck_plotpy) does, but as an app. The app allows you to start and stop recording as well as change the buffer size with a slider bar. The colors of the lines match with the colors of the pucks. When the pucks are squeezed, the blue puck will show a red line in the load cell plot and the yellow puck will show a magenta line.
![Python3 Data Plotting App](https://github.com/CaseFNI/FitMi-Data-Collection/blob/main/Media/Puck%20Data%20Plotting%20App.gif)

### puck_plot.py

Plots the x, y, and z directions of the rotational accelerometer, gyroscope, and linear acceleration; the roll, pitch, and yaw angles; and the load cell values of both pucks in a set
of subplots.

### ani_plot.py

Creates the details of the subplots needed by the [puck_plot.py](#puck_plotpy) script. This script handles the updating and modification of the subplots as well as
labeling the plots.

### show_orientation.py

Shows the x, y, and z axis of one of the pucks on a 3D plot. The sample rate and which puck is hard coded in the script.

### recording_gui.py

Logs puck data like the [log_puck_data.py](#log_puck_datapy) script, but it is more intuitive to use.
![Python3 Data Logging App](https://github.com/CaseFNI/FitMi-Data-Collection/blob/main/Media/Data%20Logging%20App.png)

### log_puck_data.py

Records the angular accelerometer, gyroscope, linear acceleration, load cell, and quaternion values of both pucks into a python dictionary, saved as a python shelf, and as a .mat file
accessible through Matlab. The sampling rate and max time of the data logging can be set and data logging can end early be pressing enter in the console where the
script was called.

## Puck Library

### hid_puck

Defines a class for handling communication to and from the dongle to the computer and the pucks. It receives a 62 byte array of information and parses that information
into the RX radio values, and the data packets for the pucks handled in the [PuckPacket](#puck_packetpy) class.

### puck_packet.py

Defines a class for parsing the data packets from each puck into angular acceleration, gyroscope, linear acceleration, quaternion, and load cell variables. This class also uses the
quaternions to find the roll, pitch, and yaw angles of the pucks.

### quaternion.py

Defines helper functions for working with quaternions.

### puck_task.py

Defines a class that specifically looks for if a puck rotates back and forth past a specific target range of angles. Im not sure if this is needed, but was provided in
the original code.

### scan_packet.py

Defines a class for analyzing the data from sending a command to scan. It tells the user how many pipe channels there are and what channel was used to scan. This isn't
used in the original code or the Python 3 code.
