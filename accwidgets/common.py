from abc import ABCMeta
from qtpy.QtCore import QObject


class AbstractQObjectMeta(type(QObject), ABCMeta):  # type: ignore
    """
    Metaclass for abstract classes based on QObject.

    A class inheriting from QObject with ABCMeta as metaclass will lead to
    an metaclass conflict:

    TypeError: metaclass conflict: the metaclass of a derived class must be
    a (non-strict) subclass of the meta-classes of all its bases
    """
    pass
