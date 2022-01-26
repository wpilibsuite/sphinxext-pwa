from typing import Any, Dict

import docutils.nodes as nodes
from sphinx.application import Sphinx


def html_page_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: Dict[str, Any],
    doctree: nodes.document,
):
    pass


def setup(app: Sphinx) -> Dict[str, Any]:

    app.connect("html-page-context", html_page_context)
    app.add_js_file()

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
