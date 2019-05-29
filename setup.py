"""
Setup file for Pip.
For user dependencies:                  pip install .
For developer additional dependencies:  pip install .[testing]
"""

import os
from typing import List, Dict
from setuptools import setup, find_packages

found_user_deps_files = []
found_dev_deps_files = []
# Files to search for -> requirements = minimal deps to run, dev_requirements = deps for running tests...
usr_deps_filename = "requirements.txt"
dev_deps_filename = "dev_requirements.txt"
dev_deps_map_key = "testing"
current_file_location = os.path.abspath(os.path.dirname(__file__))

packages = [
    "accsoft_gui_pyqt_widgets",
]
install_requires: List[str] = []
extra_requires: Dict[str, List[str]] = {
    dev_deps_map_key: [],
}

print(f"Search for files {usr_deps_filename} and {dev_deps_filename} recursively, starting from {current_file_location}")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Start Search ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
for package in packages:
    folder_to_search = current_file_location + ("" if current_file_location[-1] == os.path.sep else os.path.sep) + package
    print(f"Search folder:                     {folder_to_search}")
    for root, directories, files in os.walk(
            folder_to_search, onerror=(lambda err: print(f"{folder_to_search} not found."))):
        for file in files:
            if dev_deps_filename == file:
                print(f"Found developer requirements file: {os.path.join(root, file)}")
                found_dev_deps_files.append(os.path.join(root, file))
            elif usr_deps_filename == file:
                print(f"Found user requirements file:      {os.path.join(root, file)}")
                found_user_deps_files.append(os.path.join(root, file))

for usr_dep_file in found_user_deps_files:
    with open(os.path.join(usr_dep_file), "r") as f:
        deps = f.read().split()
        print(f"Collecting user dependencies:      {deps}")
        install_requires += deps

for dev_dep_file in found_dev_deps_files:
    with open(os.path.join(dev_dep_file), "r") as f:
        deps = f.read().split()
        print(f"Collecting developer dependencies: {deps}")
        extra_requires["testing"] += deps

print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Result of Search ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print(f"Combined user dependencies:        {install_requires}")
print(f"Combined developer dependencies:   {extra_requires}")

# raise ValueError("Stop")

setup(
    name="accsoft_gui_pyqt_widgets",
    version="0.1.0",
    description="PyQt based widgets",
    packages=find_packages(exclude=('examples', 'docs')),
    install_requires=install_requires,
    extras_require=extra_requires
)
