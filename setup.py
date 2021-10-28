"""
Setup file for Pip.
"""
import itertools
import json
import types
import importlib
import importlib.machinery
import importlib.util
from typing import Dict, List, DefaultDict, Tuple, cast, Optional, Set, Any
from collections import defaultdict
from pathlib import Path
import versioneer

from setuptools import setup, PEP420PackageFinder


# We use implicit packages (PEP420) that are not obliged
# to have __init__.py. Default implementation of setuptools.find_packages will
# expect that file to exist and thus skip everything else. We need a tailored
# version.
find_packages = PEP420PackageFinder.find

PROJECT_ROOT: Path = Path(__file__).parent.absolute()

CORE_OPTION = "core"
LINT_OPTION = "lint"
TEST_OPTION = "test"
DOC_OPTION = "doc"
EXAMPLE_OPTION = "examples"
BENCH_OPTION = "bench"
PACKAGE_NAME = "accwidgets"
EXTRAS_ALL_FEATURES = "all-widgets"
DEPENDENCY_OPTIONS = {LINT_OPTION, TEST_OPTION, BENCH_OPTION, DOC_OPTION, EXAMPLE_OPTION}
# Section for commonly defined
SHARED_OPTIONS = {LINT_OPTION, TEST_OPTION, DOC_OPTION}


REQUIREMENTS: Dict[str, List[str]] = {
    CORE_OPTION: [
        "QtPy>=1.10.0,<2a0",
        "qtawesome>=0.7.0,<2a0",
        "packaging>=20.5,<22a0",
        "deprecated>=1.2.13,<1.5a0",
        "importlib-metadata>=1.7.0,<5.0a0;python_version<'3.8'",
    ],
    LINT_OPTION: [
        "mypy==0.910",
        "numpy>=1.21",
        "types-freezegun",
        "types-Deprecated",
        "types-python-dateutil",
        "flake8>=4.0.1,<4.2a0",
        "flake8-quotes>=3.3.1,<4a0",
        "flake8-commas>=2.1.0,<3a0",
        "flake8-colors>=0.1.9,<2a0",
        "flake8-rst>=0.8.0,<2a0",
        "flake8-breakpoint>=1.1.0,<2a0",
        "flake8-pyi>=20.10.0,<21a0",
        "flake8-comprehensions>=3.7.0,<4a0",
        "flake8-builtins-unleashed>=1.3.1,<2a0",
        "flake8-blind-except>=0.2.0,<1a0",
        "flake8-bugbear>=21.9.2,<22a0",
    ],
    TEST_OPTION: [
        "pytest>=6.2.5,<7a0",
        "pytest-qt>=4.0.2,<5a0",
        "pytest-random-order>=1.0.4,<1.1a0",
        "pytest-cov>=3.0.0,<4a0",
        "pytest-asyncio>=0.16",
        "qasync>=0.13.0,<1a0",
    ],
    DOC_OPTION: [
        "Sphinx>=3.2.1,<3.5a0",
        "sphobjinv>=2.1,<3a0",
        "sphinxcontrib-napoleon2>=1.0,<2a0",
        "sphinx-autodoc-typehints>=1.12.0,<1.13a0",
        "acc-py-sphinx>=0.9,<0.10a0",
        "sphinx-copybutton>=0.4,<1a0",
        # These are simply here to provide package version in conf.py
        # If any of the widgets requires specific versions, it is expected to narrow this down
        "papc",
        "pyjapc",
        "pjlsa",
        "numpy",
        "pyqtgraph",
    ],
}


def combine_reqs() -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Parse the requirements from individual widgets and augment general requirements.
    """

    def get_reqs_file(file: Path, attr_name: str) -> Optional[Any]:
        pkg_name = f"accwidgets.{file.parent.name}.{file.stem}"
        spec: Optional[importlib.machinery.ModuleSpec] = importlib.util.spec_from_file_location(name=pkg_name,
                                                                                                location=file)
        if spec is None:
            return None
        mod: types.ModuleType = importlib.util.module_from_spec(spec)
        loader = cast(importlib.machinery.SourceFileLoader, spec.loader)

        try:
            loader.exec_module(mod)
        except ImportError:
            return None

        try:
            deps = getattr(mod, attr_name)
        except AttributeError:
            return None
        return deps

    reqs: DefaultDict[str, Set[str]] = defaultdict(set)
    reqs.update({k: set(v) for k, v in REQUIREMENTS.items()})

    for path in PROJECT_ROOT.glob("accwidgets/*/__deps__.py"):
        if not path.exists() or not path.is_file():
            continue
        print(f"Found widget requirements file {path}")
        widget_name = path.parent.name
        parsed_deps = cast(Optional[List[str]], get_reqs_file(file=path, attr_name="core"))
        if parsed_deps is None:
            continue
        widget_deps = set(parsed_deps)
        reqs[widget_name] = widget_deps
        reqs[EXTRAS_ALL_FEATURES] |= widget_deps

    for path in PROJECT_ROOT.glob("accwidgets/*/__extras__/__deps__.py"):
        if not path.exists() or not path.is_file():
            continue
        print(f"Found widget extras requirements file {path}")
        widget_extras = cast(Optional[Dict[str, List[str]]], get_reqs_file(file=path, attr_name="extras"))
        if widget_extras is None:
            continue
        for k, val in widget_extras.items():
            if k not in DEPENDENCY_OPTIONS:
                print(f"Skipping '{k}' as unsupported")
                continue
            reqs[k] |= set(val)

    for extra in DEPENDENCY_OPTIONS:
        reqs[extra] |= reqs[EXTRAS_ALL_FEATURES]

    core = reqs[CORE_OPTION]
    del reqs[CORE_OPTION]

    # Clean up more, remove duplication between core and extras
    requirements = {k: v.difference(core) for k, v in reqs.items()}

    return (list(core), {
        **{k: list(v) for k, v in requirements.items()},
        "all": list(set(itertools.chain(*requirements.values()))),
    })


install_requires, extras_require = combine_reqs()
print("Build the following requirements:\n"
      "install_requires:\n"
      f"{json.dumps(install_requires, indent=4)}\n"
      "\n"
      "extras_require:\n"
      f"{json.dumps(extras_require, indent=4)}")


setup(
    name=PACKAGE_NAME,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="PyQt-based widgets for CERN accelerator controls",
    long_description="""A collection of PyQt widgets to be used by accelerator community. This library comes
as a standalone Python package ready to be used in any PyQt application. It is also bundled by comrad, where
equivalent widgets are wrapped to provide easy access to the control system. Therefore, once integrated in
this library, a widget may shortly become available in comrad.""",
    author="Ivan Sinkarenko, Fabian Sorn",
    author_email="ivan.sinkarenko@cern.ch",
    packages=find_packages(
        exclude=("examples*",
                 "docs*",
                 "tests*",
                 "benchmarks*",
                 "coverage*",  # Produced as artifact in CI and may propagate into the final wheel
                 "build*",
                 "dist*",
                 "*.__extras__",
                 "*.egg-info")),
    url="https://wikis.cern.ch/display/ACCPY/Widgets",
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires=">=3.6,<=3.10",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: Developers",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Typing :: Typed",
    ],
    package_data={
        "": ["*.ico", "*.png", "*.ui"],
    },
    entry_points={
        "console_scripts": [
            "accwidgets-cli=_accwidgets._cli:run",
        ],
    },
    platforms=["centos7"],
    test_suite="tests",
)
