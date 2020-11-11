import inspect
import os
import sys
import importlib
import warnings
from packaging.requirements import Requirement, InvalidRequirement
from importlib_metadata import distribution, PackageNotFoundError
from pathlib import Path
from typing import Type, Set, Union


REAL_MODULE_NAME_VAR = "__accwidgets_real_module__"


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

    setattr(class_, REAL_MODULE_NAME_VAR, class_.__module__)
    class_.__module__ = public_mod_name
    setattr(class_, private_var_name, True)

    for _, nested_class in inspect.getmembers(class_, inspect.isclass):
        # Avoid random classes, allow only the ones that are declared in the subpackages of the public api
        if not nested_class.__module__.startswith(public_mod_name):
            continue
        mark_public_api(nested_class, public_mod_name)


_ASSERT_CACHE: Set[str] = set()


def assert_dependencies(base_path: Union[str, os.PathLike, Path], raise_error: bool = True):
    """
    Verifies that a given widget has all requirements installed.

    Args:
        base_path: Path to the top directory of the widget or __init__.py file inside of it.
        raise_error: Raise ImportError when :obj:`True`, otherwise issue a warning.

    Raises:
        ImportError: Requirements are not satisfied, when ``raise_error`` was set to :obj:`True`.
    """
    widget_path = Path(base_path)
    if widget_path.name == "__init__.py":
        widget_path = widget_path.parent

    if widget_path.name in _ASSERT_CACHE:
        return
    _ASSERT_CACHE.add(widget_path.name)

    pkg_name = f"accwidgets.{widget_path.name}.__deps__"
    try:
        importlib.import_module(pkg_name)
    except ImportError:
        return

    try:
        deps = sys.modules[pkg_name].core  # type: ignore
    except AttributeError:
        return

    for dep in deps:
        try:
            req = Requirement(dep)
        except InvalidRequirement as e:
            warnings.warn(f"Failed to parse dependency {dep}. This constraint will be ignored.\n{e!s}")
            continue

        try:
            assert_requirement(req=req, widget_name=widget_path.name)
        except ImportError as e:
            if raise_error:
                raise
            else:
                warnings.warn(str(e))


def assert_requirement(req: Requirement, widget_name: str):

    if req.marker and not req.marker.evaluate():
        # The environment is irrelevant for the requirement (e.g. Python version or OS)
        return

    try:
        installed_pkg = distribution(req.name)
    except PackageNotFoundError as e:
        raise ImportError(
            f'accwidgets.{widget_name} is intended to be used with "{req.name}" package. '
            f"Please specify this widget as an extra of your accwidgets dependency, e.g. accwidgets[{widget_name}] in "
            "order to keep using the widget. To quickly install it in the environment, use: "
            f"'pip install accwidgets[{widget_name}]'.\n\n{str(e)}")

    try:
        override = int(os.environ.get("ACCWIDGETS_OVERRIDE_DEPENDENCIES", 0))
    except ValueError:
        override = False
    if override:
        return

    if not req.specifier.contains(installed_pkg.version):
        raise ImportError(f"accwidgets.{widget_name} cannot reliably work with {req.name} versions other than "
                          f"{req.name}{req.specifier}. Please specify this widget as an extra of your accwidgets dependency, "
                          f"e.g. accwidgets[{widget_name}] in order to keep using the widget. To quickly install it "
                          f"in the environment, use: 'pip install accwidgets[{widget_name}]'.\n"
                          "You can override this limitation by setting an environment variable "
                          "ACCWIDGETS_OVERRIDE_DEPENDENCIES=1.")
