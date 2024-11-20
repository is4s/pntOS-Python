# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pntOS Python"
copyright = "2024, IS4S"
author = "IS4S"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser"]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
branding_dir = "../branding_assets/branding/"
html_static_path = ["../_static", branding_dir]

html_logo = branding_dir + "pntOs_Logo_Gradient_Light_Horizontal.png"
html_theme_options = {"logo_only": True}


def setup(app):
    app.add_css_file("pntos.css")
    app.add_css_file("hk-grotesk.css")
