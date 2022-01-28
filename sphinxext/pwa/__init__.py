from typing import Any, Dict, List
import os
from pathlib import Path

import docutils.nodes as nodes
from sphinx.application import Sphinx

from sphinx.util import logging

EXCLUDE_CACHE = ["_sources", ".inv", ".buildinfo"]


def get_file_list(path: str) -> List[str]:
    def get_files_recursive(path: str) -> List[str]:
        file_list = []
        for entry in os.scandir(path):
            if entry.is_dir():
                file_list.extend(get_files_recursive(entry.path))
            else:
                file_list.append(entry.path)
        return file_list

    files = get_files_recursive(path)

    # alternate version without walrus operator
    #file_list = []
    #for file in files:
    #    f = str(Path(file).relative_to(path))
    #    if not any(exclude in f for exclude in EXCLUDE_CACHE):
    #        file_list.append(f)

    return [f for file in files if not any(exclude in (f := str(Path(file).relative_to(path))) for exclude in EXCLUDE_CACHE)]


def html_page_context(
        app: Sphinx,
        pagename: str,
        templatename: str,
        context: Dict[str, Any],
        doctree: nodes.document,
) -> None:
    app.add_js_file(None, body="\"serviceWorker\"in navigator&&navigator.serviceWorker.register(\"sw.js\");", loading_method="defer")
    if doctree:
        context["metatags"] += f'<link rel="manifest" href="test-proj.webmanifest"/>'


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

    manifest = """{
  "name": "Test",
  "short_name": "Test",
  "theme_color": "#003974",
  "background_color": "#003974",
  "display": "standalone",
  "scope": "/",
  "start_url": "/index.html",
  "icons": [
  {
    "src": "/_static/first-logo-256px.png",
    "type": "image/png",
    "sizes": "256x256"
  },
  {
    "src": "/_static/first-logo-512px.png",
    "type": "image/png",
    "sizes": "512x512"
  }
  ]
}

    """

    with open(Path(app.outdir) / "test-proj.webmanifest", 'w') as manifest_file:
        manifest_file.write(manifest)


def setup(app: Sphinx) -> Dict[str, Any]:
    app.connect("html-page-context", html_page_context)
    app.connect("build-finished", build_finished)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
