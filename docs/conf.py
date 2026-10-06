import os
import sys
import django

# Add the project root to Python's path.
sys.path.insert(0, os.path.abspath(".."))

# Configure Django for Sphinx.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daily_tea.settings")
django.setup()


# -- Project information -----------------------------------------------------

project = "Daily Tea"
copyright = "2026, Daily Tea"
author = "Daily Tea Development Team"
release = "1.0"


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]

exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"

html_static_path = ["_static"]