import matplotlib.pyplot as plt
import numpy as np
import json
from os.path import join, dirname

data = json.load(open(join(dirname(__file__), "compass.json"), "r"))

# Data for plotting
t = np.array([x[0] for x in data["times"]])
s = np.array([x[1] for x in data["times"]])

fig, ax = plt.subplots()
ax.plot(t, s)

ax.set(xlabel='time (s)', ylabel='voltage (mV)',
       title='About as simple as it gets, folks')
ax.grid()

plt.show()