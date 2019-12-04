"""
Setup file for Pip.
For user dependencies:                  pip install .
For developer additional dependencies:  pip install .[testing]
"""

import os
from typing import Dict, List
from pathlib import Path
import versioneer

from setuptools import setup, PEP420PackageFinder


# We use implicit packages (PEP420) that are not obliged
# to have __init__.py. Default implementation of setuptools.find_packages will
# expect that file to exist and thus skip everything else. We need a tailored
# version.
find_packages = PEP420PackageFinder.find


FOUND_USER_DEPS_FILES = []
FOUND_DEV_DEPS_FILES = []
# Files to search for -> requirements = minimal deps to run, dev_requirements = deps for running tests...
USR_DEPS_FILENAME = "requirements.txt"
DEV_DEPS_FILENAME = "dev_requirements.txt"
DEV_DEPS_MAP_KEY = "testing"
CURRENT_FILE_LOCATION = os.path.abspath(os.path.dirname(__file__))

PACKAGES = ["accwidgets"]
INSTALL_REQUIRES: List[str] = []
EXTRA_REQUIRES: Dict[str, List[str]] = {DEV_DEPS_MAP_KEY: []}

print(
    f"Search for files {USR_DEPS_FILENAME} and {DEV_DEPS_FILENAME} recursively, starting from {CURRENT_FILE_LOCATION}"
)
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Start Search ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
for package in PACKAGES:
    folder_to_search = (
        CURRENT_FILE_LOCATION
        + ("" if CURRENT_FILE_LOCATION[-1] == os.path.sep else os.path.sep)
        + package
    )
    print(f"Search folder:                     {folder_to_search}")
    for root, directories, files in os.walk(
        folder_to_search,
        onerror=(lambda err, folder=folder_to_search: print(f"{folder} not found.")),  # type: ignore
    ):
        for file in files:
            if DEV_DEPS_FILENAME == file:
                print(f"Found developer requirements file: {os.path.join(root, file)}")
                FOUND_DEV_DEPS_FILES.append(os.path.join(root, file))
            elif USR_DEPS_FILENAME == file:
                print(f"Found user requirements file:      {os.path.join(root, file)}")
                FOUND_USER_DEPS_FILES.append(os.path.join(root, file))

for usr_dep_file in FOUND_USER_DEPS_FILES:
    with open(os.path.join(usr_dep_file), "r") as f:
        deps = f.read().split("\n")
        print(f"Collecting user dependencies:      {deps}")
        INSTALL_REQUIRES += deps

for dev_dep_file in FOUND_DEV_DEPS_FILES:
    with open(os.path.join(dev_dep_file), "r") as f:
        deps = f.read().split("\n")
        print(f"Collecting developer dependencies: {deps}")
        EXTRA_REQUIRES["testing"] += deps

EXTRA_REQUIRES["linting"] = [
    "mypy~=0.720",
    "pylint>=2.3.1&&<3",
    "pylint-unittest>=0.1.3&&<2",
    "flake8>=3.7.8&&<4",
    "flake8-quotes>=2.1.0&&<3",
    "flake8-commas>=2&&<3",
    "flake8-colors>=0.1.6&&<2",
    "flake8-rst>=0.7.1&&<2",
    "flake8-breakpoint>=1.1.0&&<2",
    "flake8-pyi>=19.3.0&&<20",
    "flake8-comprehensions>=2.2.0&&<3",
    "flake8-builtins-unleashed>=1.3.1&&<2",
    "flake8-blind-except>=0.1.1&&<2",
    "flake8-bugbear>=19.8.0&&<20",
]
EXTRA_REQUIRES["docs"] = [
    "Sphinx~=2.1.2",
    "recommonmark~=0.6.0",
    "sphinx-rtd-theme~=0.4.3",
]
EXTRA_REQUIRES["release"] = [
    "twine~=1.13.0",
    "wheel~=0.33.4",
]

curr_dir: Path = Path(__file__).parent.absolute()

with curr_dir.joinpath('README.md').open() as f:
    long_description = f.read()

setup(
    name="accwidgets",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="PyQt-based widgets for CERN accelerator controls",
    long_description=long_description,
    author='Fabian Sorn',
    author_email='fabian.sorn@cern.ch',
    packages=find_packages(exclude=("examples", "docs", "tests", "build*", "dist*", "*.egg-info")),
    url='https://wikis.cern.ch/display/ACCPY/Widgets',
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRA_REQUIRES,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Typing :: Typed',
    ],
    package_data={
        '': ['*.ico'],
    },
    platforms=['centos7'],
    test_suite='tests',
)
