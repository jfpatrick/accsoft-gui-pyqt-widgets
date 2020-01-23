"""
Modified Legend Item which allows altering the Legend Color.

TODO: remove when switching to pyqtgraph 0.11.0, since these
      issues have been addresses there.
"""

from typing import Tuple, Optional
from qtpy.QtGui import QPainter, QPen, QBrush
import pyqtgraph as pg
from pyqtgraph.graphicsItems.LegendItem import ItemSample


class ExLegendItem(pg.LegendItem):

    DEFAULT_DRAWING_TOOLS = {"bg": pg.mkBrush(0, 0, 0, 200),
                             "text": pg.mkPen(255, 255, 255, 255),
                             "border": pg.mkPen(255, 255, 255, 255)}
    """Default drawing tools"""

    def __init__(self,
                 size: Optional[Tuple[float, float]] = None,
                 offset: Optional[Tuple[float, float]] = None):
        """
        Extended version of the PyQtGraph LegendItem which allows altering
        background and text color.

        Args:
            size: Specifies the fixed size (width, height) of the legend. If
                  this argument is omitted, the legend will automatically
                  resize to fit its contents.
            offset: Specifies the offset position relative to the legend's
                    parent. Positive values offset from the left or top;
                    negative values offset from the right or bottom. If offset
                    is None, the legend must be anchored manually by calling
                    anchor() or positioned by calling setPos().
        """
        super().__init__(size=size, offset=offset)
        self._drawing_tools = self.DEFAULT_DRAWING_TOOLS.copy()

    @property
    def bg_brush(self) -> QBrush:
        """Background QColor for the legend item."""
        return self._drawing_tools.get("bg")

    @property
    def text_pen(self) -> QPen:
        """Pen used to draw the text labels."""
        return self._drawing_tools.get("text")

    @property
    def border_pen(self) -> QPen:
        """Pen used to draw the text labels."""
        return self._drawing_tools.get("border")

    def addItem(self, item: pg.GraphicsItem, name: str) -> None:
        """ Add a new entry to the legend.

        Replace addItem with a version with stronger white label for
        better visibility.

        Args:
            item: A PlotDataItem from which the line and point style
                  of the item will be determined or an instance of
                  ItemSample (or a subclass), allowing the item display
                  to be customized.
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
        """Copied version from pyqtgraph 0.11.0 Release Candidate."""
        if self.size is not None:
            return
        height = 0
        width = 0
        for sample, label in self.items:
            height += max(sample.boundingRect().height(), label.height()) + 3
            width = max(width, sample.boundingRect().width() + label.width())
        self.setGeometry(0, 0, width + 25, height)

    def paint(self, p: QPainter, *args) -> None:
        """Paint function for the Legend Item.

        Args:
            p: QPainter instance which is used for painting
        """
        p.setPen(self.border_pen)
        p.setBrush(self.bg_brush)
        p.drawRect(self.boundingRect())
