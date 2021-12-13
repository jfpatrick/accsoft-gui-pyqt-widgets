from qtpy.QtWidgets import QWidget, QMainWindow, QApplication
from qtpy.QtCore import QByteArray, QBuffer, QIODevice


def grab_png_screenshot(source: QWidget, include_window_decorations: bool) -> bytes:
    """
    Takes screenshot of a given widget and stores it in a byte array with png compression.

    Args:
        source: Widget to grab screenshot of.
        include_window_decorations: When source is :class:`QMainWindow`, this allows to
                                    include window frame in the screenshot.

    Returns:
        Byte array of the *.png image.
    """
    if isinstance(source, QMainWindow) and include_window_decorations:
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0,
                                       source.pos().x(),
                                       source.pos().y(),
                                       source.frameGeometry().width(),
                                       source.frameGeometry().height())
    else:
        screenshot = source.grab()
    img_bytes = QByteArray()
    img_buf = QBuffer(img_bytes)
    img_buf.open(QIODevice.WriteOnly)
    screenshot.save(img_buf, "png", quality=100)
    return img_bytes
