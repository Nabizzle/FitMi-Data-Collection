##----------------------------------------------------------------------------##
##---- plot logged data ------------------------------------------------------##
##----------------------------------------------------------------------------##

import matplotlib.pyplot as plt
import numpy as np
import os
import shelve

data_folder = os.path.join(os.getcwd(), "data")
fname = input("enter the name of the file you want to plot (without extension): ")
fname += ".shelve"
fullpath = os.path.join(data_folder, fname)
print(fullpath)

if not os.path.exists(fullpath):
    error_string = "%s not found" % fullpath
    raise Exception(error_string)

data_shelf = shelve.open(fullpath)

print(data_shelf.keys())

for key in data_shelf.keys():
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(data_shelf[key])
    ax.set_title(key)
    fig.show()

data_shelf.close()

input("press enter to close all")
