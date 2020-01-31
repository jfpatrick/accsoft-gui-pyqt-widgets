"""
Module with code for keeping track if we are currently located in
a Qt Designer environment using a global variable

**Attention:** Import statements of this module have to be exactly
the same, so no absolute and relative imports mixed. Otherwise python
will load this module multiple times under different names and _IS_DESIGNER
will exist multiple times.
"""

_IS_DESIGNER = False


def is_designer() -> bool:
    """Check, if code has been run from designer"""
    global _IS_DESIGNER
    return _IS_DESIGNER


def set_designer() -> None:
    """Call to set flag, that code has been run from designer"""
    global _IS_DESIGNER
    _IS_DESIGNER = True
