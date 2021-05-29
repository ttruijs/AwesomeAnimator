import numpy as np
import multiprocessing as mp
import matplotlib.pyplot as plt
import time
from abc import ABC, abstractmethod
from typing import List, Tuple
from collections import namedtuple

Msg = namedtuple("Msg", ["animator_index", "plot_index", "data"])

class Animator(ABC):

    @abstractmethod
    def init_animation(self):
        """
        All matplotlib stuff is initialised over here,
        so as to create the plots on the same process as the AWESOMEANIMATOR.
        """
        pass

    @abstractmethod
    def update(self):
        """
        Update the plot when necessary.
        """
        pass

class PlotAnimator(Animator):

    def __init__(self, nrows, ncols, max_history):
        super().__init__()
        self.nrows = nrows
        self.ncols = ncols
        self.max_history = max_history

    def init_animation(self):
        self.fig, self.axes = plt.subplots(self.nrows, self.ncols)

        if self.nrows != 1 and self.ncols != 1:
            self.axes = [ax for axs in self.axes for ax in axs]
        elif self.nrows == 1 and self.ncols == 1:
            self.axes = [self.axes]

        self.lines = []
        for i in range(self.nrows*self.ncols):
            line, = self.axes[i].plot(np.zeros(self.max_history))
            self.lines += [line]

        self.data = [np.zeros(self.max_history) for j in range(self.nrows*self.ncols)]

    def update(self, plot_index, data):
        self.data[plot_index] = np.roll(self.data[plot_index], -1)
        self.data[plot_index][-1] = data
        self.lines[plot_index].set_ydata(self.data[plot_index])

        minimum, maximum = np.min(self.data[plot_index]), np.max(self.data[plot_index])
        vertlen = maximum-minimum
        self.axes[plot_index].set_ylim(minimum-.1*abs(vertlen), maximum+.1*abs(vertlen))

class ImageAnimator(Animator):

    def __init__(self, nrows: int, ncols: int, cmaps: List[str] = None):
        self.nrows= nrows
        self.ncols = ncols
        self.cmaps = cmaps

    def init_animation(self):
        self.fig, self.axes = plt.subplots(self.nrows, self.ncols)

        if self.nrows != 1 and self.ncols != 1:
            self.axes = [ax for axs in self.axes for ax in axs]
        elif self.nrows == 1 and self.ncols == 1:
            self.axes = [self.axes]

        if self.cmaps == None:
            for ax in self.axes:
                ax.imshow(np.zeros((1, 1)))
        else:
            for ax, cmap in zip(self.axes, self.cmaps):
                ax.imshow(np.zeros((1, 1)), cmap=cmap)

    def update(self, plot_index, data):
        if self.cmaps == None:
            self.axes[plot_index].imshow(data)
        else:
            self.axes[plot_index].imshow(data, cmap=self.cmaps[plot_index])

class AwesomeAnimator(mp.Process):

    def __init__(self, animators: List[Animator], interval: float = 0):
        """
        Welcome to the crib.
        """
        super().__init__()
        self.animators = animators
        self.q = mp.Queue()
        self.interval = interval

    def push(self, animator_index, plot_index, data):
        """
        Send some shit to the queue.
        """
        msg = Msg(animator_index, plot_index, data)
        self.q.put(msg)

    def run(self):
        """
        This is where the magic happens.
        """
        for animator in self.animators:
            animator.init_animation()
        while True:
            while not self.q.empty():
                msg = self.q.get()
                self.animators[msg.animator_index].update(msg.plot_index, msg.data)
            for animator in self.animators:
                animator.fig.canvas.draw()
            plt.pause(.0001)
            time.sleep(self.interval)

if __name__ == "__main__":
    ani = ImageAnimator(1, 1, cmaps=['RdBu'])
    ani2 = PlotAnimator(1, 2, 100)
    p = AwesomeAnimator([ani, ani2], 2)
    p.start()
    p.push(0, 0, np.array([[i for i in range(32)] for j in range(32)]))
    while True:
        p.push(1, 0, np.random.randint(0, 2))
        p.push(1, 1, np.random.randint(0, 100)*.01)
        time.sleep(1)
    p.join()

