# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pntOS Python'
copyright = '2024, IS4S'
author = 'IS4S'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['myst_parser', 'sphinx.ext.napoleon', 'sphinx.ext.autodoc']

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# autodoc options
autodoc_member_order = 'bysource'
autodoc_default_options = {
    'show-inheritance': True,
}
autodoc_preserve_defaults = True
autodoc_typehints = 'none'
autodoc_typehints_description_target = 'documented'

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
branding_dir = '../branding_assets/branding/'
html_static_path = ['../_static', branding_dir]

html_logo = branding_dir + 'pntOs_Logo_Gradient_Light_Horizontal.png'
html_theme_options = {'logo_only': True}


def setup(app):
    app.add_css_file('pntos.css')
    app.add_css_file('hk-grotesk.css')
