from typing import Any, Dict, List
import os
from pathlib import Path

import docutils.nodes as nodes
from sphinx.application import Sphinx

from sphinx.util import logging

EXCLUDE_CACHE = ["_sources"]


def get_file_list(path: str) -> List[str]:
    file_list = []
    for entry in os.scandir(path):
        if not any(exclude in entry.path for exclude in EXCLUDE_CACHE):
            file_list.append(entry.path)
            if entry.is_dir():
                file_list.extend(get_file_list(entry.path))
    return file_list


def html_page_context(
        app: Sphinx,
        pagename: str,
        templatename: str,
        context: Dict[str, Any],
        doctree: nodes.document,
) -> None:
    app.add_js_file("/sw.js", loading_method="defer")


def build_finished(
        app: Sphinx,
        exc: Exception
) -> None:
    logger = logging.getLogger(__name__)
    logger.info(app.outdir)
    file_list = get_file_list(app.outdir)
    sw = """self.addEventListener('install', function(e) {
    e.waitUntil(
        caches.open('frc-docs').then(function(cache) {
            return cache.addAll([
                """+"'"+"',\n'".join(file_list)+"'"+"""
            ]);
        })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
            return response || fetch(event.request);
        })
    );
});"""
    with open(Path(app.outdir) / "sw.js", 'w') as sw_file:
        sw_file.write(sw)


def setup(app: Sphinx) -> Dict[str, Any]:
    app.connect("html-page-context", html_page_context)
    app.connect("build-finished", build_finished)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
