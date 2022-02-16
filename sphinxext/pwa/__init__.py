import warnings
from typing import Any, Dict, List
from pathlib import Path
from warnings import warn
import mimetypes
import os
import json
import random

from sphinx.application import Sphinx
from sphinx.errors import ConfigError
from docutils import nodes
from urllib.parse import urljoin, urlparse, urlunparse
from sphinx.util import logging


logger = logging.getLogger(__name__)


def get_cache(path: str, baseurl: str, exclude: List[str]) -> List[str]:
    url = baseurl
    # we have to use absolute urls in our cache resource, because fetch will return an absolute url
    # this means that we cannot accurately cache resources that are in PRs because RTD does not give us
    # the url
    # readthedocs uses html_baseurl for sphinx > 1.8
    if baseurl is not None:
        parse_result = urlparse(url)

        # enables RTD multilanguage support
        if os.getenv("READTHEDOCS"):
            parse_result.path = (
                os.getenv("READTHEDOCS_LANGUAGE")
                + "/"
                + os.getenv("READTHEDOCS_VERSION")
            )

        url = urlunparse(parse_result)
    elif baseurl is None:
        logger.warning(
            "html_baseurl is not configured. This can be ignored if deployed in RTD environments."
        )

    def _walk(_path: str) -> List[str]:
        _file_list = []
        for entry in os.scandir(_path):
            rel_path = str(Path(entry.path).relative_to(path))
            # exclude all files that match exclude
            if any(e in rel_path for e in exclude):
                pass

            if entry.is_dir():
                _file_list.extend(_walk(entry.path))
            else:
                _file_list.append(urljoin(url, rel_path))

        return _file_list

    return _walk(path)


def get_manifest(config: Dict[str, Any]) -> Dict[str, str]:
    if config["pwa-icons"] is None:
        raise ConfigError("Icons are required for PWAs!")

    icons = []

    for path, sizes in config["pwa_icons"]:
        mime_type = mimetypes.guess_type(path)[0]
        if mime_type is None:
            raise ConfigError("Specified image is unrecognized type: " + path)
        # todo possibly only allow a subset of mime types

        icons.append({"src": path, "type": mime_type, "sizes": sizes})

    return {
        "name": config["pwa_name"],
        "short_name": config["pwa_short_name"],
        "theme_color": config["pwa_theme_color"],
        "background_color": config["pwa_background_color"],
        "display": config["pwa_display"],
        "scope": "../",
        "start_url": f"../{config['root_doc']}.html",
        "icons": [],
    }


def generate_files(app: Sphinx, config: Dict[str, Any]) -> None:
    static_dir = Path(app.outdir, "_static")
    cache_list = get_cache(app.outdir, config["html_baseurl"], ["_static", "sw.js"])
    service_worker = (Path(__file__).parent / "pwa_service_files" / "sw.js").read_text()

    logger.info(config["root_doc"])

    service_worker.replace(
        "{{% CACHE-NAME %}}", "sphinx-app" + str(random.randrange(10000, 100000))
    )

    with open(static_dir / "app.webmanifest", "w") as f:
        json.dump(get_manifest(config), f)

    with open(static_dir / "cache.json", "w") as f:
        json.dump(cache_list, f)


def build_finished(app: Sphinx, exception: Exception):
    if exception is None:
        generate_files(app, app.config)


def html_page_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: Dict[str, Any],
    doctree: nodes.document,
) -> None:
    # todo possible cleanup
    if doctree and pagename == app.config["root_doc"]:
        context["metatags"] += (
            '\n<script>"serviceWorker"in navigator&&navigator.serviceWorker.register("sw.js").catch(e=>window.alert(e));</script>'
            + '\n<link rel="manifest" href="_static/app.webmanifest"/>'
        )

        if icon := app.config["pwa_apple_icon"] is not None:
            context["metatags"] += f'<link rel="apple-touch-icon" href="{icon}">'


def setup(app: Sphinx) -> Dict[str, Any]:
    # todo Do all these values need a rebuild?
    app.add_config_value("pwa_name", app.config.project, "html")
    app.add_config_value("pwa_short_name", app.config.project, "html")
    app.add_config_value("pwa_theme_color", "", "html")
    app.add_config_value("pwa_background_color", "", "html")
    app.add_config_value("pwa_display", "standalone", "html")
    app.add_config_value(
        "pwa_icons", None, "html", [Dict]
    )  # todo make sure this does something
    app.add_config_value("pwa_apple_icon", "", "html")

    app.connect("html-page-context", html_page_context)
    app.connect("build-finished", build_finished)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
