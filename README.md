# accwidgets

Accelerator Widgets for Python GUIs (accwidgets)

>
> **[Read user documentation](https://acc-py.web.cern.ch/gitlab/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets/docs/stable)**
>

From here on, the information is related to the development of the library...

# Contents
- [Description](#description)
- [Test](#test)
- [Development](#development)
  - [Linting](#linting)
  - [Building documentation](#building-documentation)
  - [Uploading package to CO package index](#uploading-package-to-co-package-index)

# Description

*accwidgets* is a library of widgets. While common dependencies are listed in the library metadata,
certain widgets may require additional dependencies, such as PyJAPC. Depending of what is being used for
the application, developer may need to install such dependencies manually, referring to the requirements
of used widgets. The library is designed to work with [PyQt distribution](https://wikis.cern.ch/display/ACCPY/PyQt+distribution)
offered as a part of "Accelerating Python" initiative. It is also assuming the use of virtual
environments.

# Test

Considering that you have installed the package from source, navigate to the root directory,
and prepare test dependencies
```bash
pip install -e .[test]
```

Next, run tests:

```bash
python -m pytest
```

>
**Note!** Testing can be done in the randomized order to make sure that mocking does not
affect adjacent tests. To run in random order,
```bash
python -m pytest --random-order
```
>


# Development

For development, the easiest is to install all possible packages (to skip `pip install` in the
subsections):
```bash
pip install -e .[all]
```

You may want to benefit from `pre-commit` tool, which is already installed with dependencies above. The only additional
step to activate it is to run:
```bash
pre-commit install
```

>
> **[Read contributing guide](https://acc-py.web.cern.ch/gitlab/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets/docs/stable/contrib/index.html)**
>

## Linting

*accwidgets* is integrated with several linting utilities:

- [flake8](https://pypi.org/project/flake8/)
- [mypy](https://pypi.org/project/mypy/)

(we intentionally do not use [pylint](https://pypi.org/project/pylint/) because it creates too
much overhead)

Install required packages first:
```bash
pip install -e .[lint]
```

You would run each of them separately (from repository root).

For flake8:
```bash
flake8
```

For mypy (it does not handle PEP420 packages, so you'd need to specify them as arguments):
```bash
mypy . docs examples
```

## Building documentation

Install required packages first:
```bash
pip install -e .[doc]
```

Use [Sphinx](http://www.sphinx-doc.org/en/master/) to build the docs:
```bash
sphinx-build docs/ path/to/docs/output/dir
```

To browse it, just locate the `index.html`:
```bash
xdg-open path/to/docs/output/dir/index.html
```

Cross-referencing "Intersphinx" plugin takes heavy advantage of custom inventories
to create links for third-party libraries, such as Qt, PyQt and others. Not all of them
are available in the friendly way, that's why we have few custom inventories (located in
`docs/*.inv` files). These files are packaged using [sphobjinv](https://pypi.org/project/sphobjinv/)
tool from corresponding `docs/*.txt` files. If you want to add a missing symbol, modify
the `*.txt` file, re-create the inventory:
```bash
sphobjinv convert zlib --overwrite docs/<lib>.txt docs/<lib>.inv
```

Follow [this page](https://sphobjinv.readthedocs.io/en/v2.0/syntax.html) to understand the inventory
format.

## Uploading package to CO package index

**Note! Normally, this is done automatically by the CI pipeline, as long as there's a git tag pushed
(tag must follow vX.X.X format, because it will influence the version reported by published package).
No additional actions are needed! If you want to perform the sequence manually, follow the steps.**

Make sure that you have tools installed
```bash
pip install twine wheel build
```
Prepare the source distribution
```bash
# Build sdist
python -m build --sdist .
# Build wheel
mkdir -p dist && cd dist && pip wheel ../ --no-deps && cd ../
```

Upload to the repository
```bash
python -m twine upload --repository-url http://acc-py-repo.cern.ch:8081/repository/py-release-local/ -u py-service-upload dist/*
```

And now you can clean up
```bash
rm -rf build dist *.egg-info
```
