"""
Two benchmarks which allow the comparison between two live curves,
one with AccGraph and the other one done with pure PyQtGraph.

To execute, type (with widgetmark being installed):
$ widgetmark bench_live_curve.py
"""
from typing import List

import widgetmark
import accwidgets.graph as accgraph
import pyqtgraph as pg
import numpy as np


class AccGraphLiveCurve(widgetmark.UseCase):

    backend = widgetmark.GuiBackend.QT
    goal = 25.0
    minimum = 10.0
    tolerance = 0.05
    repeat = 10000
    parameters = {
        "curves": [1, 5, 10],
        "size": [1000, 10000, 100000],
    }

    def setup_widget(self):
        self._widget = accgraph.ScrollingPlotWidget(time_span=10)
        self._sources = [accgraph.UpdateSource() for _ in range(self.curves)]
        self._curves = [self._widget.addCurve(
            data_source=s,
            buffer_size=int(1.5 * self.size),
        ) for s in self._sources]
        for i, s in enumerate(self._sources):
            x = np.linspace(0, 10, self.size)
            y = np.sin(x) + i
            s.new_data(accgraph.CurveData(x, y))
        return self._widget

    def operate(self):
        x = (self.runtime_context.current_run + self.size) / (self.size / 10)
        y = np.sin(x)
        for i, s in enumerate(self._sources):
            point = accgraph.PointData(x, y + i)
            s.new_data(data=point)


class PyQtGraphLiveCurve(widgetmark.UseCase):

    backend = widgetmark.GuiBackend.QT
    goal = 25.0
    minimum = 10.0
    tolerance = 0.05
    repeat = 10000
    parameters = {
        "curves": [1, 5, 10],
        "size": [1000, 10000, 100000],
    }

    def setup_widget(self):
        self._widget = pg.PlotWidget()
        self._curves: List[pg.PlotDataItem] = []
        self._data: List[List[float]] = []
        for i in range(self.curves):
            x = np.linspace(0, 10, self.size)
            y = np.sin(x) + i
            curve = pg.PlotDataItem(x, y)
            self._widget.addItem(curve)
            self._data.append([x, y])
            self._curves.append(curve)
        return self._widget

    def operate(self):
        x = (self.runtime_context.current_run + self.size) / (self.size / 10)
        y = np.sin(x)
        for i, c in enumerate(self._curves):
            self._data[i][0] = np.roll(self._data[i][0], -1)
            self._data[i][0][-1] = x
            self._data[i][1] = np.roll(self._data[i][1], -1)
            self._data[i][1][-1] = y + i
            c.setData(self._data[i][0], self._data[i][1])
