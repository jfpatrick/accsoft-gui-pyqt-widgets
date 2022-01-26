import pytest
from PIL import Image, ImageChops
from pathlib import Path
from pytestqt.qtbot import QtBot
from unittest import mock
from qtpy.QtCore import QSize, QByteArray, QRect
from qtpy.QtWidgets import QWidget, QMainWindow
from qtpy.QtGui import QBitmap, QImageWriter
from accwidgets.screenshot._grabber import grab_png_screenshot, get_pixmap, pixmap_to_png_bytes


class CustomWindow(QMainWindow):
    pass


class CustomWidget(QWidget):
    pass


@pytest.mark.parametrize("src_type,decor,should_call_grab,should_call_grab_window", [
    (QWidget, False, True, False),
    (QWidget, True, True, False),
    (CustomWidget, False, True, False),
    (CustomWidget, True, True, False),
    (QMainWindow, False, True, False),
    (QMainWindow, True, False, True),
    (CustomWindow, False, True, False),
    (CustomWindow, True, False, True),
])
@mock.patch("qtpy.QtGui.QScreen.grabWindow")
@mock.patch("qtpy.QtWidgets.QWidget.grab")
def test_get_pixmap_uses_screen_api_for_decorations(grab, grabWindow, qtbot: QtBot, src_type, decor, should_call_grab,
                                                    should_call_grab_window):
    source = src_type()
    qtbot.add_widget(source)
    res = get_pixmap(source=source, include_window_decorations=decor)
    if should_call_grab:
        grab.assert_called_once()
        assert res is grab.return_value
    else:
        grab.assert_not_called()
    if should_call_grab_window:
        grabWindow.assert_called_once()
        assert res is grabWindow.return_value
    else:
        grabWindow.assert_not_called()


@pytest.mark.parametrize("geometry,frame_geometry,expected_args", [
    ([0, 0, 200, 100], [0, 0, 200, 100], [0, 0, 200, 100]),
    ([0, 0, 100, 200], [0, 0, 100, 200], [0, 0, 100, 200]),
    ([50, 100, 200, 100], [50, 100, 200, 100], [0, 0, 200, 100]),
    ([50, 100, 200, 100], [50, 80, 200, 120], [0, -20, 200, 120]),
    ([50, 100, 200, 100], [20, 80, 260, 140], [-30, -20, 260, 140]),
])
@mock.patch("qtpy.QtWidgets.QApplication.primaryScreen")
def test_window_decor_calculates_offsets(primaryScreen, qtbot: QtBot, geometry, frame_geometry, expected_args):
    grabWindow = primaryScreen.return_value.grabWindow
    source = QMainWindow()
    qtbot.add_widget(source)
    with mock.patch.object(source, "winId") as winId:
        with mock.patch.object(source, "geometry", return_value=QRect(*geometry)):
            with mock.patch.object(source, "frameGeometry", return_value=QRect(*frame_geometry)):
                get_pixmap(source=source, include_window_decorations=True)
                grabWindow.assert_called_once_with(winId.return_value, *expected_args)


@pytest.mark.parametrize("width,height,image_filename,input_bytes", [
    (
        5, 5,
        "image1.png",
        bytes([100, 125, 0, 1, 49,
               67, 34, 23, 55, 64,
               0, 0, 100, 102, 4,
               67, 34, 23, 55, 64,
               67, 34, 23, 55, 64]),
    ),
    (
        3, 3,
        "image2.png",
        bytes([0, 1, 49,
               0, 0, 0,
               67, 34, 23]),
    ),
])
def test_pixmap_to_png_bytes(qapp, width, height, input_bytes, image_filename):
    _ = qapp
    size = QSize(width, height)
    pixmap = QBitmap.fromData(size, input_bytes)
    res = pixmap_to_png_bytes(pixmap)
    assert isinstance(res, (QByteArray, bytes))

    # Comparing byte array may fail, because actual produced bytes may differ (e.g. the ones produced on dev
    # machine in Gnome slightly differ from headless CI. Therefore, we use Python Imaging Library to compare
    # differences. (When no differences, bounding box will be empty)
    actual = Image.frombytes(mode="L", size=(width, height), data=res)
    reference = Image.open(Path(__file__).parent / "images" / image_filename)
    diff = ImageChops.difference(actual, reference)
    assert not diff.getbbox()


@pytest.mark.parametrize("src_type", [QWidget, QMainWindow])
@pytest.mark.parametrize("decor", [True, False])
@mock.patch("accwidgets.screenshot._grabber.pixmap_to_png_bytes")
@mock.patch("accwidgets.screenshot._grabber.get_pixmap")
def test_grab_png_screenshot(pixmap_mock, mocked_converter, qtbot: QtBot, decor, src_type):
    px = mock.MagicMock()
    pixmap_mock.return_value = px
    converted = mock.MagicMock()
    mocked_converter.return_value = converted
    source = src_type()
    qtbot.add_widget(source)
    res = grab_png_screenshot(source=source, include_window_decorations=decor)
    pixmap_mock.assert_called_once_with(source=source, include_window_decorations=decor)
    mocked_converter.assert_called_once_with(px)
    assert res is converted


def test_png_is_supported_by_qt(qapp):
    _ = qapp
    assert b"png" in QImageWriter.supportedImageFormats()
