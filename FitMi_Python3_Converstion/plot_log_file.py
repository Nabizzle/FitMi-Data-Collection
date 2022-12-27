##----------------------------------------------------------------------------##
##---- plot logged data ------------------------------------------------------##
##----------------------------------------------------------------------------##

import matplotlib.pyplot as plt
import numpy as np
import os
import shelve

datafolder = os.path.join(os.getcwd(), "data")
fname = raw_input("enter the name of the file you want to plot (without extension): ")
fname += ".shelve"
fullpath = os.path.join(datafolder, fname)
print fullpath

if not os.path.exists(fullpath):
    errorstr = "%s not found" % fullpath
    raise Exception(errorstr)

datash = shelve.open(fullpath)

print datash.keys()

for key in datash.keys():
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(datash[key])
    ax.set_title(key)
    fig.show()

datash.close()

raw_input("press enter to close all")
