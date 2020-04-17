"""
Setup file for Pip.
"""
import itertools
from typing import Dict, List, Union, DefaultDict
from collections import defaultdict
from pathlib import Path
import versioneer
import configparser  # For requirements parsing

from setuptools import setup, PEP420PackageFinder


# We use implicit packages (PEP420) that are not obliged
# to have __init__.py. Default implementation of setuptools.find_packages will
# expect that file to exist and thus skip everything else. We need a tailored
# version.
find_packages = PEP420PackageFinder.find

PROJECT_ROOT: Path = Path(__file__).parent.absolute()

PACKAGE_NAME = "accwidgets"
# File defining reuqirements
DEPENDENCY_FILE = "dependencies.ini"
# Dependency Options for widget depdendencies
DEPENDENCY_OPTIONS = {"core", "test", "bench", "doc"}
# Section for commonly defined
SHARED_OPTIONS = {"lint", "release"}


def parse_requirements() -> Dict[str, Union[List[str], Dict[str, List[str]]]]:
    """
    Parse the requirements from the requirement ini file and combine them
    for setuptools.
    """
    config = configparser.ConfigParser()
    config.read(PROJECT_ROOT / DEPENDENCY_FILE)
    requirements: DefaultDict[str, List[str]] = defaultdict(list)
    parsed_reqs = lambda section: [r.strip(", ") for r in section.splitlines()]
    # Shared project dependencies
    for option in SHARED_OPTIONS:
        package_reqs = config.get(PACKAGE_NAME, option, fallback="")
        requirements[option] = parsed_reqs(package_reqs)
    config.remove_section(PACKAGE_NAME)
    # Widget dependencies
    sections = config.sections()
    print(f"Found following sections in dependency file: {sections}.")
    for section in sections:
        print(f"Found following Options in Section '{section}': "
              f"{list(dict(config[section]))}")
        for option in dict(config[section]):
            if option not in DEPENDENCY_OPTIONS:
                raise Exception(
                    f"Invalid dependency option '{option}' was found in "
                    f"section '{section}', supported are only "
                    f"following options: {', '.join(DEPENDENCY_OPTIONS)}.")
            requirement_string = config.get(section,
                                            option,
                                            fallback="")
            widget_reqs = parsed_reqs(requirement_string)
            requirements[option].extend(widget_reqs)
    return {
        "core": requirements["core"],
        "extra": {
            **requirements,
            "dev": requirements["test"] + requirements["lint"],
            "all": list(itertools.chain(*requirements.values())),
        },
    }


REQUIREMENTS = parse_requirements()
print(f"Requirements after parsing: {REQUIREMENTS}")


# Readme -> Long Description
with PROJECT_ROOT.joinpath("README.md").open() as f:
    long_description = f.read()

setup(
    name=PACKAGE_NAME,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="PyQt-based widgets for CERN accelerator controls",
    long_description=long_description,
    author="Ivan Sinkarenko, Fabian Sorn",
    author_email="ivan.sinkarenko@cern.ch",
    packages=find_packages(
        exclude=("examples*",
                 "docs*",
                 "tests*",
                 "benchmarks*",
                 "build*",
                 "dist*",
                 "*.egg-info")),
    url="https://wikis.cern.ch/display/ACCPY/Widgets",
    install_requires=REQUIREMENTS["core"],
    extras_require=REQUIREMENTS["extra"],
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
    platforms=["centos7"],
    test_suite="tests",
)
