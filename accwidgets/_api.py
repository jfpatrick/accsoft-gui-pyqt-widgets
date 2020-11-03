import inspect
from typing import Type


def mark_public_api(class_: Type, public_mod_name: str):
    """
    Mark the class to as coming canonically from this module rather
    than from the nested definition location.

    Args:
        class_: Class to tamper with.
    """
    if not inspect.isclass(class_):
        return

    private_var_name = f"__{class_.__name__}_accwidgets_public_api__"

    if getattr(class_, private_var_name, False):
        return

    class_.__module__ = public_mod_name
    setattr(class_, private_var_name, True)

    for _, nested_class in inspect.getmembers(class_, inspect.isclass):
        # Avoid random classes, allow only the ones that are declared in the subpackages of the public api
        if not nested_class.__module__.startswith(public_mod_name):
            continue
        mark_public_api(nested_class, public_mod_name)
