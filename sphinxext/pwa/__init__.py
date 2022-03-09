import subprocess
from sys import stderr
from typing import Any, Dict, List
from pathlib import Path
import mimetypes
import os
import json

from sphinx.application import Sphinx
from sphinx.errors import ConfigError
from docutils import nodes
from urllib.parse import urljoin
from sphinx.util import logging

logger = logging.getLogger(__name__)


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
        "start_url": f"../{config['root_doc']}.html?pwa",
        "icons": icons,
    }


def generate_files(app: Sphinx, config: Dict[str, Any]) -> None:
    static_dir = Path(app.outdir, "_static")

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
        install_result = subprocess.check_call(
            "npm install workbox-cli --global",
            shell=True,
        )

        logger.info("Successfully installed workbox!")
        return True
    else:
        return True


def build_finished(app: Sphinx, exception: Exception):
    if exception is None:
        generate_files(app, app.config)

        if does_node_exist() and not app.config["pwa_online_only"]:
            if does_workbox_exist():
                os.chdir(app.outdir)
                logger.info("Generating service worker files!")

                success = subprocess.check_call(
                    "workbox generateSW workbox-config.js",
                    shell=True,
                )
                logger.info("Successfully generated service worker files!")
        else:
            logger.info("Running in Online-Only mode!")


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
                if ('serviceWorker' in navigator) {
                    // Use the window load event to keep the page load performant
                    window.addEventListener('load', () => {
                        if (urlParams.has('pwa')) {
                            console.log("Installing PWA!");
                            navigator.serviceWorker.register('sw.js');
                        } else {
                            console.log("Standalone mode not detected!");
                        }
                });
            }
            </script>
            <link rel="manifest" href="_static/app.webmanifest"/>
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
    app.add_config_value("pwa_online_only", False, "html")

    app.connect("html-page-context", html_page_context)
    app.connect("build-finished", build_finished)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
