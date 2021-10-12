"""
This module stays for backwards compatibility, but :class:`accwidgets.graph.ExLegendItem` is no longer needed`.
"""

import pyqtgraph as pg
from deprecated import deprecated
from qtpy.QtGui import QBrush, QPen, QColor


@deprecated(reason="ExLegendItem's functionality is now fully covered by native pyqtgraph's legendItem.")
class ExLegendItem(pg.LegendItem):
    """Deprecated! ExLegendItem's functionality is now fully covered by native pyqtgraph's legendItem. Please use it."""

    DEFAULT_DRAWING_TOOLS = {
        "bg": QBrush(QColor(0, 0, 0, 100)),
        "border": QPen(QColor(255, 255, 255, 100)),
        "text": QPen(QColor(255, 255, 255, 100)),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    bg_brush = property(fget=pg.LegendItem.brush, fset=pg.LegendItem.setBrush)

    border_pen = property(fget=pg.LegendItem.pen, fset=pg.LegendItem.setPen)

    @property
    def text_pen(self) -> QPen:
        return QPen(self.labelTextColor())

    @text_pen.setter
    def text_pen(self, new_val: QPen):
        self.setLabelTextColor(new_val.color())

    remove_item_from_legend = pg.LegendItem.removeItem
