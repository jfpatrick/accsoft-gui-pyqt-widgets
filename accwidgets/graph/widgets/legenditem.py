"""
This module provides modified :class:`~pyqtgraph.LegendItem` that permits altering legend colors.

.. note:: This module will become irrelevant when library will be rebased on pyqtgraph v0.11.0.
"""

# TODO: remove when switching to pyqtgraph>=0.11.0, since these issues have been addresses there.

import pyqtgraph as pg
from typing import Tuple, Optional
from qtpy.QtGui import QPainter, QPen, QBrush
from pyqtgraph.graphicsItems.LegendItem import ItemSample


class ExLegendItem(pg.LegendItem):

    DEFAULT_DRAWING_TOOLS = {"bg": pg.mkBrush(0, 0, 0, 200),
                             "text": pg.mkPen(255, 255, 255, 255),
                             "border": pg.mkPen(255, 255, 255, 255)}
    """Mapping of the default properties applied to the legend items."""

    def __init__(self,
                 size: Optional[Tuple[float, float]] = None,
                 offset: Optional[Tuple[float, float]] = None):
        """
        Extended version of the :class:`pyqtgraph.LegendItem` that allows altering
        background and text colors.

        Args:
            size: Specifies the fixed size ``(width, height)`` of the legend. If
                  this argument is omitted, the legend will automatically
                  resize to fit its contents.
            offset: Specifies the offset position relative to the legend's
                    parent.

                    * Positive values offset from the left or top
                    * Negative values offset from the right or bottom
                    * If offset is :obj:`None`, the legend must be anchored
                      manually by calling :meth:`anchor` or positioned by calling :meth:`setPos`.
        """
        super().__init__(size=size, offset=offset)
        self._drawing_tools = self.DEFAULT_DRAWING_TOOLS.copy()

    @property
    def bg_brush(self) -> QBrush:
        """Brush specifying the background color for the legend item."""
        return self._drawing_tools.get("bg")

    @property
    def text_pen(self) -> QPen:
        """Pen used to draw the text labels."""
        return self._drawing_tools.get("text")

    @property
    def border_pen(self) -> QPen:
        """Pen used to draw the border frame."""
        return self._drawing_tools.get("border")

    def addItem(self, item: pg.GraphicsItem, name: str):
        """
        Add a new entry to the legend.

        This replaces :meth:`pyqtgraph.LegendItem.addItem` with a version with stronger
        white label for better visibility.

        Args:
            item: A :class:`~pyqtgraph.PlotDataItem` from which the line and point style
                  of the item will be determined or an instance of
                  :class:`ItemSample` (or a subclass),
                  allowing the item display to be customized.
            name: The title to display for this item. Simple HTML allowed.
        """
        label = pg.LabelItem(text=name,
                             color=self.text_pen.color(),
                             justify="left")  # Changed to left alignment
        if isinstance(item, ItemSample):
            sample = item
        else:
            sample = ItemSample(item)
        row = self.layout.rowCount()
        self.items.append((sample, label))
        self.layout.addItem(sample, row, 0)
        self.layout.addItem(label, row, 1)
        self.updateSize()

    def updateSize(self):
        """
        Updates legend's geometry to fit the items.

        **Note!** This implementation is copied from ``pyqtgraph==0.11.0rc1``.
        """
        if self.size is not None:
            return
        height = 0
        width = 0
        for sample, label in self.items:
            height += max(sample.boundingRect().height(), label.height()) + 3
            width = max(width, sample.boundingRect().width() + label.width())
        self.setGeometry(0, 0, width + 25, height)

    def remove_item_from_legend(self, item: Tuple[ItemSample, pg.LabelItem]):
        """
        Removes one item from the legend.

        In contrast to :meth:`removeItem`, this method takes the tuple,
        that can be extracted from ``self.items`` without figuring out its label.

        Args:
            item: Tuple, as directly can be extracted from ``self.items``.
        """
        sample, label = item
        # This code pretty much matches :meth:`~pyqtgraph.LegendItem.removeItem`.
        self.items.remove(item)    # remove from itemlist
        self.layout.removeItem(sample)          # remove from layout
        sample.close()                          # remove from drawing
        self.layout.removeItem(label)
        label.close()
        self.updateSize()                       # redraq box

    def paint(self, p: QPainter, *args):
        """
        This function, which is usually called by :class:`QGraphicsView`, paints the contents of an item
        in local coordinates.

        Args:
            p: Painter that is used for painting. `See details <https://doc.qt.io/qt-5/paintsystem.html>__`.
        """
        p.setPen(self.border_pen)
        p.setBrush(self.bg_brush)
        p.drawRect(self.boundingRect())
