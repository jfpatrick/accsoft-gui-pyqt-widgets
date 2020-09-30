Development guidelines
======================

- `Linting, Type-Checking, and Formatting`_
- `Testing`_

  * `Running Tests`_
  * `Test coverage`_

- `Documenting the widget`_

  * `Generating documentation`_

- `CI Integration`_


We follow
`Acc-Py development guidelines <https://wikis.cern.ch/display/ACCPY/Development+Guidelines#DevelopmentGuidelines-CodingConventions>`__.


Linting, Type-Checking, and Formatting
--------------------------------------

The first aid for every Python developer is linting tools. For this purpose we use `flake8 <https://gitlab.com/pycqa/flake8>`__
and `mypy <http://www.mypy-lang.org/>`__ packages to run linting and type-checking over our code respectively.

.. todo:: Future may see a common coding style powered by `auto formatters <https://issues.cern.ch/browse/ACCPY-427>`__.


Testing
-------

Automated testing is a must for good software. Besides obvious assurance that your code does not break with the next
change, very often it makes you reason about the architecture in a better way, making code decoupled and thus more
maintainable.

We use `pytest <https://docs.pytest.org/en/latest/>`__ along with few plugins:

- `pytest-cov <https://pytest-cov.readthedocs.io/en/latest/>`__ helps to keep track of any code that is not yet covered by tests.
- `pytest-random-order <https://pythonhosted.org/pytest-random-order/>`__ allows you to shuffle test execution on each run to make sure that all tests are completely independent of each other.
- `pytest-qt <https://pytest-qt.readthedocs.io/en/latest/index.html>`__ provides a fixture with which you can write tests for PyQt applications.

Running Tests
^^^^^^^^^^^^^

.. note:: Remember to install the test dependencies before running tests.

.. code-block:: bash

   cd /path/to/accsoft-gui-pyqt-widgets
   pip install .[test]
   # Run tests in a randomized order and check code coverage
   pytest --random-order --cov-report term-missing:skip-covered --cov=accwidgets tests/


Test coverage
^^^^^^^^^^^^^

Test coverage gives you an idea of how well your code base is tested. It is also useful to see the evolution of test
coverage over a period of time (when used with CI).

While test coverage is a useful tool, it should not become the goal:

- Code coverage does not guarantee that all possible scenarios are tested. It is your responsibility to foresee all
  use-cases, no matter how likely they are.
- 100% code coverage is often an unreachable goal and may lead to code being transformed into less usable, yet more covered.


Documenting the widget
----------------------

To make your widgets easy to use, good documentation is mandatory. Documentation comes from 4 channels:

- **Using Python type hints**: By doing so, you are helping IDE to give meaningful context-specific information to the
  user during coding. They also play well with the docstrings, so you don't need to duplicate type information in the docstring.
- **Generating API reference**: For this, Python docstrings are necessary for all public classes, methods, and variables.
  We use `Google Style docstrings <http://google.github.io/styleguide/pyguide.html>`__ (if you have documented your code
  in a different style, try converting it with `pyment <http://daouzli.com/blog/pyment.html>`__). Make sure to document
  all arguments and return values in method/function docstrings.
- **Writing the documentation by hand**: This is useful for explaining concepts and giving examples that cannot be
  linked to a single specific place in the code. This documentation can be included in generated documentation to be
  hosted on the server.
- **Providing interactive examples**: You'd be giving newcomers a feel of how what your widget is capable of and
  teaching how to use it by example. Make sure to keep the examples simple to not overwhelm users with unnecessary
  complexity. Better include multiple examples with a single use-case instead of one trying to cover all possible use-cases.


Generating documentation
^^^^^^^^^^^^^^^^^^^^^^^^

`Sphinx <http://www.sphinx-doc.org/en/master/>`__ allows you to generate documentation for your widgets based on
docstrings from your code and additionally hand-written reStructuredText files. The documentation is hosted by
`Acc-Py documentation server <https://acc-py.web.cern.ch/gitlab/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets/docs/stable/>`__
and is generated automatically using CI for tagged releases and main branches (develop & master). You can build
documentation locally using ``sphinx-build`` command.


CI Integration
--------------

CI allows us to automate linting, testing and generating documentation. It is great for general regression testing,
as well as brings value to the Merge Request-based workflow. Tests are performed on MR submission, as well as after
the merge, ensuring that things do not break suddenly. That being said, CI is helpless without good test suite.
Hence, do not pass on writing extensive tests for your contributions.
