import functools
import warnings
from typing import Dict, Any, Callable


def deprecated_param_alias(**aliases: str) -> Callable:
    """
    Deprecation alias allows defining aliases for deprecated function
    parameters.

    Args:
        aliases: Mapping of deprecated parameter to the new parameter name
                 in the form old_name='new_name'
    """
    def deco(f: Callable):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            _rename_kwargs(f.__name__, kwargs, aliases)
            return f(*args, **kwargs)
        return wrapper
    return deco


def _rename_kwargs(func_name: str,
                   kwargs: Dict[str, Any],
                   aliases: Dict[str, Any]):
    """
    Rename received keyword arguments.

    Args:
        func_name: Name of the function which's arguments are wrapped
        kwargs: Keyword Arguments passed to the function which was wrapped
        aliases: Aliases mapping the old kwarg names to the new ones
    """
    for alias, new in aliases.items():
        if alias in kwargs:
            if new in kwargs:
                raise TypeError(f"'{func_name}' received both '{alias}' "
                                f"and '{new}'")
            warnings.warn(f"Keyword-argument '{alias}' in function "
                          f"'{func_name}' is deprecated, use '{new}'.",
                          DeprecationWarning)
            kwargs[new] = kwargs.pop(alias)
