"""
Setup file for Pip.
For user dependencies:                  pip install .
For developer additional dependencies:  pip install .[testing]
"""

import os
from typing import Dict, List

from setuptools import find_packages, setup

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

print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Result of Search ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print(f"Combined user dependencies:        {INSTALL_REQUIRES}")
print(f"Combined developer dependencies:   {EXTRA_REQUIRES}")

# raise ValueError("Stop")

setup(
    name="accwidgets",
    version="0.1.0",
    description="PyQt based widgets",
    packages=find_packages(exclude=("examples", "docs", "tests")),
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRA_REQUIRES,
)
