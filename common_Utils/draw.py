import sys

platform = sys.platform
if platform.startswith('linux'):
    import matplotlib
    matplotlib.use('Agg')

import matplotlib.pyplot as plt

class Draw(object):
    def __init__(self, x, y, xlabel, ylabel, title, legend, outputname):
        '''
        This is the Draw class for evaluation system
        Author : Siqi Qin
        :param x: x axis data, should be a list of input, eg: [[x1_0 ..... x1_n], [x2_0 ..... x2_m]]
        :param y: y axis data, should be a list of input
        :param xlabel: x axis label
        :param ylabel: y axis label
        :param title: title for the graph
        :param legend: legend for the graph
        :param outputname: desired output name
        '''
        self._x = x
        self._y = y
        self._xlabel = xlabel
        self._ylabel = ylabel
        self._title = title
        self._legend = legend
        self._outputname = outputname

    def show(self):
        fig = plt.figure()
        assert len(self._x) == len(self._y)
        for i in range(len(self._x)):
            plt.plot(self._x[i], self._y[i])
        plt.xlabel(self._xlabel)
        plt.ylabel(self._ylabel)
        plt.title(self._title)
        plt.grid()
        if len(self._x) > 1:
            plt.legend(self._legend)
        fig.savefig(self._outputname)
        plt.close(fig)