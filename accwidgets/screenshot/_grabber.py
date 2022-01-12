from qtpy.QtWidgets import QWidget, QMainWindow, QApplication
from qtpy.QtCore import QByteArray, QBuffer, QIODevice
from qtpy.QtGui import QPixmap


def grab_png_screenshot(source: QWidget, include_window_decorations: bool) -> bytes:
    pixmap = get_pixmap(source=source, include_window_decorations=include_window_decorations)
    return pixmap_to_png_bytes(pixmap)


def get_pixmap(source: QWidget, include_window_decorations: bool) -> QPixmap:
    if not include_window_decorations or not isinstance(source, QMainWindow):
        return source.grab()
    screen = QApplication.primaryScreen()
    x_offset = source.geometry().x() - source.frameGeometry().x()
    y_offset = source.geometry().y() - source.frameGeometry().y()
    return screen.grabWindow(source.winId(),
                             -x_offset,
                             -y_offset,
                             source.frameGeometry().width(),
                             source.frameGeometry().height())


def pixmap_to_png_bytes(pixmap: QPixmap) -> bytes:
    img_bytes = QByteArray()
    img_buf = QBuffer(img_bytes)
    img_buf.open(QIODevice.WriteOnly)
    pixmap.save(img_buf, "png", quality=100)
    return img_bytes
