"""General Purpose Utility functions."""

import functools
from typing import Optional, Type, Callable
import warnings


def warn_always(warning_type: Optional[Type[Warning]] = None) -> Callable:
    """
    Decorator for raising warnings each time they appear. When no warning type
    is passed, all warning types will be risen always.

    Args:
        warning_type: Warning type which should be risen each time
    """
    def deco(f: Callable):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if warning_type is not None and issubclass(warning_type, Warning):
                warnings.simplefilter("always", category=warning_type)
            else:
                warnings.simplefilter("always")
            return_val = f(*args, **kwargs)
            warnings.resetwarnings()
            return return_val
        return wrapper
    return deco
