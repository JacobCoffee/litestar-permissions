"""Sphinx configuration for litestar-permissions documentation."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "litestar-permissions"
copyright = "2025, Jacob Coffee"
author = "Jacob Coffee"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_iconify",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "shibuya"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_title = "litestar-permissions"

html_theme_options = {
    "accent_color": "tomato",
    "github_url": "https://github.com/JacobCoffee/litestar-permissions",
    "nav_links": [
        {"title": "Litestar", "url": "https://litestar.dev/"},
        {"title": "PyPI", "url": "https://pypi.org/project/litestar-permissions/"},
    ],
}

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
autodoc_typehints = "description"
autodoc_class_signature = "separated"
autodoc_inherit_docstrings = True

autosummary_generate = True

# sphinx_autodoc_typehints: set TYPE_CHECKING = True so guarded imports resolve
set_type_checking_flag = True
always_use_bars_union = True
typehints_fully_qualified = False

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_attr_annotations = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "litestar": ("https://docs.litestar.dev/latest/", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3

copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True

suppress_warnings = [
    "myst.xref_missing",
    "ref.duplicate_object",
    "misc.highlighting_failure",
    "sphinx_autodoc_typehints.forward_reference",
]

nitpicky = False


def setup(app: object) -> None:
    """Register stub roles/directives used in upstream (SQLAlchemy) docstrings."""
    from docutils import nodes
    from docutils.parsers.rst import Directive, directives, roles

    def paramref_role(_name: str, _rawtext: str, text: str, _lineno: int, _inliner: object, **_: object) -> tuple:
        return [nodes.literal(text, text)], []

    roles.register_local_role("paramref", paramref_role)

    class LegacyDirective(Directive):
        has_content = True
        optional_arguments = 1
        final_argument_whitespace = True

        def run(self) -> list:
            return []

    directives.register_directive("legacy", LegacyDirective)
