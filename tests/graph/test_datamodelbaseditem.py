from accwidgets.graph import PlotWidgetStyle, DataModelBasedItem


def test_datamodelbaseditem_subclass_pickup():

    # BaseClass
    class A:
        supported_plotting_style: PlotWidgetStyle = None  # type: ignore

    # Defines Plotting Style -> Should be picked up
    class B(A):
        supported_plotting_style = PlotWidgetStyle.STATIC_PLOT

    # Does not define a Plotting Style -> Should not be picked up
    class C(A):
        pass

    # Defines Plotting Style -> Should be picked up
    class D(C):
        supported_plotting_style = PlotWidgetStyle.SCROLLING_PLOT

    # Defines Plotting Style -> Should be picked up
    class E(C):
        supported_plotting_style = PlotWidgetStyle.CYCLIC_PLOT

    # Inherits Plotting Style from parent -> Should not be picked up
    class F(D):
        pass

    actual = DataModelBasedItem.plotting_style_subclasses(A)
    # No duplicate values
    assert len(actual) == len(set(actual))
    # picked up right classes
    assert set(actual) == {B, D, E}
