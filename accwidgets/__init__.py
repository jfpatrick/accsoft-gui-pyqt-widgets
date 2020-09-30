"""
A collection of PyQt widgets to be used by accelerator community. This library comes as a standalone
Python package ready to be used in any PyQt application. It is also bundled by :mod:`comrad`,
where equivalent widgets are wrapped to provide easy access to the control system. Therefore, once
integrated in this library, a widget may shortly become available in :mod:`comrad`.
"""

from ._version import get_versions
__version__ = get_versions()["version"]
del get_versions
