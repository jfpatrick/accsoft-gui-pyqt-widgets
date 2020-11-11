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
RELEASE_OPTION = "release"
DOC_OPTION = "doc"
BENCH_OPTION = "bench"
PACKAGE_NAME = "accwidgets"
EXTRAS_ALL_FEATURES = "all-widgets"
DEPENDENCY_OPTIONS = {LINT_OPTION, TEST_OPTION, BENCH_OPTION, DOC_OPTION}
# Section for commonly defined
SHARED_OPTIONS = {LINT_OPTION, RELEASE_OPTION, TEST_OPTION, DOC_OPTION}


REQUIREMENTS: Dict[str, List[str]] = {
    CORE_OPTION: [
        "QtPy>=1.7,<2a0",
        "packaging>=20.4,<20.5a0",
        "importlib-metadata>=1.7.0,<1.8a0",
    ],
    LINT_OPTION: [
        "mypy==0.761",
        "flake8>=3.7.8,<3.8a0",
        "flake8-quotes>=2.1.0,<3a0",
        "flake8-commas>=2,<3a0",
        "flake8-colors>=0.1.6,<2a0",
        "flake8-rst>=0.7.1,<2a0",
        "flake8-breakpoint>=1.1.0,<2a0",
        "flake8-pyi>=19.3.0,<20a0",
        "flake8-comprehensions>=2.2.0,<3a0",
        "flake8-builtins-unleashed>=1.3.1,<2a0",
        "flake8-blind-except>=0.1.1,<2a0",
        "flake8-bugbear>=19.8.0,<20a0",
    ],
    RELEASE_OPTION: [
        "twine>=1.13.0,<1.14a0",
    ],
    TEST_OPTION: [
        "pytest>=4.4.0,<4.5a0",
        "pytest-qt>=3.2.0,<3.3a0",
        "pytest-random-order>=1.0.4,<1.1a0",
        "pytest-cov>=2.5.1,<2.6a0",
    ],
    DOC_OPTION: [
        "Sphinx>=3.2.1,<3.3a0",
        "sphobjinv>=2.0,<2.1a0",
        "sphinxcontrib-napoleon2>=1.0,<2a0",
        "sphinx-autodoc-typehints>=1.10.3,<1.11a0",
        "acc-py-sphinx>=0.9,<0.10a0",
    ],
}


def combine_reqs() -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Parse the requirements from individual widgets and augment general requirements.
    """

    def get_reqs_file(file: Path, attr_name: str) -> Optional[Any]:
        pkg_name = f"accwidgets.{file.parent.name}.{file.stem}"
        spec: importlib.machinery.ModuleSpec = importlib.util.spec_from_file_location(name=pkg_name, location=file)
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
                 "build*",
                 "dist*",
                 "*.__extras__",
                 "*.egg-info")),
    url="https://wikis.cern.ch/display/ACCPY/Widgets",
    install_requires=install_requires,
    extras_require=extras_require,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: Developers",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Typing :: Typed",
    ],
    package_data={
        "": ["*.ico", "*.ui"],
    },
    entry_points={
        "console_scripts": [
            "accwidgets_designer_path=_accwidgets._designer_path:run",
        ],
    },
    platforms=["centos7"],
    test_suite="tests",
)
