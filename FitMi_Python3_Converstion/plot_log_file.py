'''
Plots data from the a log file.

Takes in a Python data file and plots each of the data types to their own plot.

Parameters
----------
data_folder : file path
    Path to the data folder
file_name : string
    name of the data file
full_path : file path
    Path to the data file
error_string : string
    error message if the path to the file does not exist
data_shelf : python data file
    data from the log file
fig : matplotlib.pyplot figure
    figure for each data type
ax : matplotlib.pyplot axis
    axis for a data plot
'''
import matplotlib.pyplot as plt
import os
import shelve

# get the path to the data folder
data_folder = os.path.join(os.getcwd(), "data")

# ask for the data file name and add the right extension
file_name = input("enter the name of the file you want to plot: ")
file_name += ".shelve"

# create the file path to the data file
full_path = os.path.join(data_folder, file_name)
print(full_path)

# check if the data file path exists
if not os.path.exists(full_path):
    error_string = "%s not found" % full_path
    raise Exception(error_string)

# get the data from the log file
data_shelf = shelve.open(full_path)

# show the user the data types in the log file
print(data_shelf.keys())

# make a plot for each data type
for key in data_shelf.keys():
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(data_shelf[key])
    ax.set_title(key)
    fig.show()

data_shelf.close() # close the data file

input("press enter to close all") # wait for user to end the script
