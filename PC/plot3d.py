import pandas as pd 
import matplotlib.pyplot as plt 
from matplotlib.animation import FuncAnimation

ax = plt.axes(projection='3d')
filename = 'data3D.csv'
header1='x'
header2='y'
header3='z'


def animate(i):
    data = pd.read_csv(filename)
    x = data[header1]
    y = data[header2]
    z = data[header3]

    plt.cla()
    ax.plot3D(x,y,z,'red')

ani = FuncAnimation(plt.gcf(),animate,interval=5)
plt.tight_layout()
plt.show()
