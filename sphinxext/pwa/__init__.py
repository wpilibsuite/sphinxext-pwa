import subprocess
from sys import stderr
from typing import Any, Dict, List
from pathlib import Path
import mimetypes
import os
import json
import random

from sphinx.application import Sphinx
from sphinx.errors import ConfigError
from docutils import nodes
from urllib.parse import urljoin
from sphinx.util import logging

logger = logging.getLogger(__name__)


def get_cache(path: str, baseurl: str, exclude: List[str]) -> List[str]:
    url = baseurl
    # we have to use absolute urls in our cache resource, because fetch will return an absolute url
    # this means that we cannot accurately cache resources that are in PRs because RTD does not give us
    # the url
    # readthedocs uses html_baseurl for sphinx > 1.8
    # enables RTD multilanguage support (todo fixup comments and make sure this still works)
    if baseurl is None:
        logger.warning(
            "html_baseurl is not configured. This can be ignored if deployed in RTD environments."
        )
    elif os.getenv("READTHEDOCS"):
        url = urljoin(
            url,
            os.getenv("READTHEDOCS_LANGUAGE") + "/" + os.getenv("READTHEDOCS_VERSION"),
        )

    def _walk(_path: str) -> List[str]:
        _file_list = []
        for entry in os.scandir(_path):
            rel_path = str(Path(entry.path).relative_to(path))
            # exclude all files that match exclude
            if any(e in rel_path for e in exclude):
                continue

            if entry.is_dir():
                _file_list.extend(_walk(entry.path))
            else:
                _file_list.append(urljoin(url, rel_path))

        return _file_list

    return _walk(path)


def get_manifest(config: Dict[str, Any]) -> Dict[str, str]:
    if config["pwa_icons"] is None:
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
        "icons": icons,
    }


def generate_files(app: Sphinx, config: Dict[str, Any]) -> None:
    static_dir = Path(app.outdir, "_static")
    cache_list = get_cache(
        app.outdir,
        config["html_baseurl"],
        ["_sources", "sw.js"] + config["pwa_exclude_cache"],
    )

    # Make the service worker and replace the cache name
    service_worker = (
        Path(__file__).parent / "pwa_service_files" / "workbox-config.js"
    ).read_text()
    Path(app.outdir, "workbox-config.js").write_text(service_worker)

    with open(static_dir / "app.webmanifest", "w") as f:
        json.dump(get_manifest(config), f)


def does_node_exist():
    success = subprocess.run(["node", "-v"], stdout=subprocess.PIPE)

    if success.returncode != 0:
        logger.warning("Unable to run Node. Is it installed? Running in Online Mode.")
        return False
    else:
        return True


# verify workbox exists or is installed
# if it is not, install it
def does_workbox_exist():
    success = subprocess.run(
        ["workbox"],
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if success.returncode != 0 and success.returncode != 2:
        logger.info("Workbox is not installed. Attempting installation!")
        install_result = subprocess.run(
            ["npm", "install", "workbox-cli"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            shell=True,
        )

        if install_result.returncode != 0:
            logger.error(
                "Failed to install workbox-cli with error", install_result.stderr
            )
            return False
        else:
            logger.info("Successfully installed workbox!")
            return True
    else:
        return True


def build_finished(app: Sphinx, exception: Exception):
    if exception is None:
        generate_files(app, app.config)

        if does_node_exist():
            if does_workbox_exist():
                os.chdir(app.outdir)
                logger.info("Generating service worker files!")

                success = subprocess.run(
                    ["workbox", "generateSW", "workbox-config.js"],
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                    shell=True,
                )

                if success.returncode != 0:
                    logger.error(
                        "Failed to generate service worker files", success.stdout
                    )
                else:
                    logger.info("Successfully generated service worker files!")


def html_page_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: Dict[str, Any],
    doctree: nodes.document,
) -> None:
    # todo possible cleanup
    if doctree and pagename == app.config["root_doc"]:
        context[
            "metatags"
        ] += """
            <script>
                const queryString = window.location.search;
                const urlParams = new URLSearchParams(queryString);
                // Check that service workers are supported
                if ('serviceWorker' in navigator && urlParams.has('pwa')) {
                    // Use the window load event to keep the page load performant
                    window.addEventListener('load', () => {
                        navigator.serviceWorker.register('/service-worker.js');
                });
            }
            </script>
            """

        if icon := app.config["pwa_apple_icon"] is not None:
            context["metatags"] += f'<link rel="apple-touch-icon" href="{icon}">'


def setup(app: Sphinx) -> Dict[str, Any]:
    # todo Do all these values need a rebuild?
    app.add_config_value("pwa_name", app.config.project, "html")
    app.add_config_value("pwa_short_name", app.config.project, "html")
    app.add_config_value("pwa_theme_color", "", "html")
    app.add_config_value("pwa_background_color", "", "html")
    app.add_config_value("pwa_display", "standalone", "html")
    app.add_config_value("pwa_icons", None, "html")
    app.add_config_value("pwa_exclude_cache", [], "html")
    app.add_config_value("pwa_apple_icon", "", "html")

    app.connect("html-page-context", html_page_context)
    app.connect("build-finished", build_finished)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
