# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# In our case we have to point Sphinx to the accwidgets package
# which is located two directories upwards.

from datetime import datetime
from accwidgets import __version__

# -- Project information -----------------------------------------------------

project = "accwidgets"
copyright = f"{datetime.now().year}, CERN"
author = "BE-CO"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_rtd_theme",  # Read-the-docs theme
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to sphinx_doc directory, that match files and
# directories to ignore when looking for sphinx_doc files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

html_short_title = f"{project} v{__version__}"
html_title = f"{html_short_title} docs"

# This value controls the docstrings inheritance. If set to True the docstring for classes or methods,
# if not explicitly set, is inherited form parents.
autodoc_inherit_docstrings = True
# Scan all found documents for autosummary directives, and generate stub pages for each.
autosummary_generate = True
# Document classes and functions imported in modules
autosummary_imported_members = True
# if True, set typing.TYPE_CHECKING to True to enable “expensive” typing imports
set_type_checking_flag = True

# Skip putting module names in front of classes, since we already have the
# structure reflected in the module name
add_module_names = False
