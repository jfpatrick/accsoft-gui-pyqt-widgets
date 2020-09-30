from enum import IntEnum


class PlotWidgetStyle(IntEnum):
    """Styles of data representation an ExPlotWidget offers."""

    STATIC_PLOT = 0
    """Static plotting with pure PyQtGraph plotting items."""
    SCROLLING_PLOT = 1
    """
    New data gets appended and old one cut. This creates
    a scrolling movement of the graph in positive x direction
    """
    CYCLIC_PLOT = 2
    """
    A moving line redraws periodically an non moving line graph. The old
    version gets overdrawn as soon as a new point exists that is plotted
    to the same position in x range. The curve is not moving in x direction
    since its x range is fixed.
    """
    EDITABLE = 3
    """
    Editable charts allow manipulating the data displayed by a curve and
    sending it back to the process it originally came from. The plot will have
    two states, a normal mode, where interaction with the plot will behave
    as with a static one, and a editing mode, in which dragging on the plot
    selects data points in a curve which should be edited.
    """
