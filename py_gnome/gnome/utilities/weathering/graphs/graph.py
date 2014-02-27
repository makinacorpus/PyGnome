#!/usr/bin/env python
"""
A MatPlotLib graphing class.
Here we encapsulate the built-in API of MatPlotLib and pyplot into a class
that is hopefully easier to use.
(Note: there is a rich graphing package called seaborn that piggybacks on
       top of MatPlotLib which we may eventually want to use.)

One very important reason for making this class, besides ease of use, is that
MatPlotLib objects can not be directly persisted into a formatted file.
On the mpl forums that I have visited, most have suggested that the data be
persisted if it is difficult to reproduce, and a plot be generated from data
when needed.

The data needed for graphing is contained in this class, and a render() method
acts upon the contained data.  Thus, this class, along with py_gnomes
persistence infrastructure, will allow us to save and recall graph objects
from cache, as well as serialize and deserialize them.

This is meant to be a usable base class that behaves in a general manner.
But it is also intended to be easily customizable through sub-classing.
"""
from uuid import uuid1

import numpy
np = numpy

import matplotlib
mpl = matplotlib
from matplotlib import pyplot

plt = pyplot


class Graph(object):
    default_labels = 'XYZABCDEFGHJKLMNPQRSTUVW'

    def __init__(self, points, labels='', formats=None, title='Title'):
        '''
           :param points: A sequence of data points for us to graph.
           :type points:  Sequence of data point items in the form:
                          ((X1, X2, X3, ... XN),
                           (S1(1), S1(2), S1(3), ... S1(N))
                           ...
                           (SN(1), SN(2), SN(3), ... SN(N))
                           )
                          where the first item contains the X axis we will use,
                          followed by 1 or more sequences of series data to be
                          plotted on the Y axis.
           :param labels: A list of labels to be used with our series
                          data sets.  If labels are not given, then we
                          use default labels.
           :param formats: An optional list of pyplot format strings to be used
                           with our series data sets.
        '''
        self.points = points
        self.labels = labels
        self.formats = formats
        self.title = title
        self.fig_num = uuid1()

    def __del__(self):
        '''
           The entire python session could be shutting down at this point,
           so don't assume anything exists externally to our object
        '''
        if plt:
            plt.close(self.fig_num)

    def render(self):
        self._init_figure()
        self._plot_points()
        self._label_xaxis()
        self._label_yaxis()
        self._make_legend()

        plt.title(self.title)
        plt.show()

    def _init_figure(self):
        '''
           - opening the figure by fig_num will reuse any existing figure.
             So we will simply open the figure by number
           - It will probably be OK to just clear the figure every time.
        '''
        self.fig = plt.figure(num=self.fig_num)
        self.fig.clear()

    def _plot_points(self):
        '''
           There are lots of plotting styles that we may want to take advantage
           of here.  But for right now, we just get it plotted.
           TODO: We may need to utilize labels here in order to get the Legend
                 going properly.
        '''
        x = self.points[0]
        for p, i in zip(self.points, range(len(self.points)))[1:]:
            static_args = [x, p]

            if self.formats and len(self.formats) > i:
                static_args.append(self.formats[i])

            plt.plot(*static_args, **self._get_styles(i))

    def _get_styles(self, idx):
        ret = {}
        ret['label'] = self._get_label(idx)

        return ret

    def _get_label(self, idx):
        try:
            return self.labels[idx]
        except IndexError:
                return self.default_labels[idx]

    def _label_xaxis(self):
            plt.xlabel(self._get_label(0))

    def _label_yaxis(self):
        '''
           We label the Y axis only if we are dealing with a single series.
           Otherwise, it doesn't really make sense.
        '''
        if len(self.points) == 2:
            plt.ylabel(self._get_label(1))

    def _make_legend(self):
        if len(self.points) > 2:
            plt.legend(loc='upper center', shadow=True)


if __name__ == '__main__':
    print 'Starting some simple tests for our graph...'
    plt.switch_backend('macosx')

    dg = Graph(points=((1, 2, 3),
                       (2, 3, 4),),
               labels=('t',),
               title='Only X Axis label customized'
               )
    dg.render()

    dg = Graph(points=((1, 2, 3),
                       (2, 3, 4),),
               labels=('t', 'F(t)'),
               title='Both X and Y Axis labels customized'
               )
    dg.render()

    dg = Graph(points=((1, 2, 3),
                       (2, 3, 4),
                       (3, 4, 5),),
               labels=('t',),
               title='No Y Axis label'
               )
    dg.render()

    dg = Graph(points=((1, 2, 3),
                       (2, 3, 4),
                       (3, 4, 5),),
               labels=('t', 'Series 1', 'Series 2'),
               title='Custom legend labels'
               )
    dg.render()

    dg = Graph(points=((1, 2, 3),
                       (2, 3, 4),
                       (3, 4, 5),),
               labels=('x', 'F1(x)', 'F2(x)'),
               formats=('', 'r-o', 'g->'),
               title='Custom line styles'
               )
    dg.render()
