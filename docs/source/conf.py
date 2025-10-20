from shutil import copytree, rmtree
from site import getsitepackages

from sphinx.application import Sphinx

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pntOS Python'
copyright = '2025, IS4S'
author = 'IS4S'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx_design',
    'sphinx_copybutton',
]

# Myst settings
myst_enable_extensions = [
    'dollarmath',  # For inline and block math using $...$
    'amsmath',  # For LaTeX dmath
    'attrs_inline',  # For inline attributes on things like images
    'colon_fence',  # Allow :::{note} syntax, making it easier to have code in notes
]
myst_heading_anchors = 3

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
    'members': True,
    'imported-members': True,
}
autodoc_preserve_defaults = True
autodoc_typehints = 'none'
autodoc_typehints_description_target = 'documented'
autodoc_warningiserror = True

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
site_packages_dir = getsitepackages()[0]
branding_dir = f'{site_packages_dir}/branding/'

# Copy images from site packages into docs directory
rmtree('images', ignore_errors=True)
copytree(src=branding_dir + '/figures/', dst='images')

html_static_path = ['../_static', branding_dir]

html_logo = branding_dir + 'pntOs_Logo_Gradient_Light_Horizontal.png'
html_theme_options = {
    'logo_only': True,
    'collapse_navigation': True,
}
html_favicon = f'{branding_dir}/favicon.ico'

nitpicky = True
nitpick_ignore = [
    # Core Python classes which automodule automatically tries to link to.
    ('py:class', 'abc.ABC'),
    ('py:class', 'optional'),
    ('py:class', 'enum.Enum'),
    # numpy classes which automodule automatically tries to link to.
    ('py:class', 'float64'),
    ('py:class', 'NDArray'),
    # A ASPN-Python classes which automodule automatically tries to link to.
    ('py:class', 'AspnBase'),
    ('py:class', 'MeasurementImu'),
    ('py:class', 'MeasurementImuImuType'),
    ('py:class', 'MeasurementPositionVelocityAttitude'),
    ('py:class', 'TypeHeader'),
    ('py:class', 'TypeTimestamp'),
    ('py:class', 'aspn23_xtensor.AspnMeasurementImuImuType'),
    ('py:class', 'aspn23_xtensor.AspnMessageType'),
    ('py:class', 'aspn23_xtensor.MeasurementImu'),
    ('py:class', 'aspn23_xtensor.MeasurementPositionVelocityAttitude'),
    ('py:class', 'aspn23_xtensor.TypeHeader'),
    ('py:class', 'aspn23_xtensor.TypeTimestamp'),
    # A NavToolkit class which automodule automatically tries to link to.
    ('py:class', 'ImuModel'),
    # Potentially caused by #49.
    ('py:class', 'PluginType'),
    ('py:class', 'ConfigType'),
    ('py:class', 'InertialType'),
    ('py:class', 'InitializationType'),
    ('py:class', 'StateModelProviderType'),
    ('py:class', 'FusionStrategyType'),
    ('py:class', 'FusionEngineType'),
    ('py:class', 'pntos.api.RegistryValueTypeUnion'),
    ('py:obj', 'pntos.api.RegistryValueTypeUnion'),
    ('py:class', 'RegistryValueType'),
    ('py:class', 'RegistryValueTypeUnion'),
    ('py:class', 'pathlib.Path'),
]

# Linkcheck builder options.
linkcheck_allowed_redirects = {
    # All redirections to the sign-in page will be counted as "working".
    r'.*git.aspn.us.*': r'https://git.aspn.us/users/sign_in'
}
# Ignore line number anchors (e.g. #L12), since linkcheck gives false positives for these.
linkcheck_anchors_ignore = [r'L\d*']


def setup(app: Sphinx) -> None:
    app.add_css_file('pntos.css')
    app.add_css_file('hk-grotesk.css')
