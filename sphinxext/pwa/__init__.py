import sphinx as Sphinx
from typing import Any, Dict, List
import os
from docutils import nodes
import json
import random
import shutil
from urllib.parse import urljoin, urlparse, urlunparse
from sphinx.util import logging
from sphinx.util.console import green, red, yellow  # pylint: disable=no-name-in-module

manifest = {
    "name": "",
    "short_name": "",
    "theme_color": "",
    "background_color": "",
    "display": "standalone",
    "scope": "../",
    "start_url": "../index.html",
    "icons": [],
}

logger = logging.getLogger(__name__)


def get_files_to_cache(outDir: str, config: Dict[str, Any]):
    files_to_cache = []
    for (dirpath, dirname, filenames) in os.walk(outDir):
        dirpath = dirpath.split(outDir)[1]

        # skip adding sources to cache
        if os.sep + "_sources" + os.sep in dirpath:
            continue

        # add files to cache
        for name in filenames:
            if "sw.js" in name:
                continue

            dirpath = dirpath.replace("\\", "/")
            dirpath = dirpath.lstrip("/")

            # we have to use absolute urls in our cache resource, because fetch will return an absolute url
            # this means that we cannot accurately cache resources that are in PRs because RTD does not give us
            # the url
            if config["html_baseurl"] is not None:
                # readthedocs uses html_baseurl for sphinx > 1.8
                parse_result = urlparse(config["html_baseurl"])

                # Grab root url from canonical url
                url = parse_result.netloc

                # enables RTD multilanguage support
                # manually create the url, because urljoin strips
                # https and only takes two params
                if os.getenv("READTHEDOCS"):
                    url = (
                        "https://"
                        + url
                        + "/"
                        + os.getenv("READTHEDOCS_LANGUAGE")
                        + "/"
                        + os.getenv("READTHEDOCS_VERSION")
                        + "/"
                    )

            if config["html_baseurl"] is None and not os.getenv("CI"):
                logger.warning(
                    red(
                        f"html_baseurl is not configured. This can be ignored if deployed in RTD environments."
                    )
                )
                url = ""

            if dirpath == "":
                resource_url = urljoin(url, name)
                files_to_cache.append(resource_url)
            else:
                resource_url = url + dirpath + "/" + name
                files_to_cache.append(resource_url)

    return files_to_cache


def build_finished(app: Sphinx, exception: Exception):
    outDir = app.outdir
    config = app.config
    outDirStatic = outDir + os.sep + "_static" + os.sep
    files_to_cache = get_files_to_cache(outDir, app.config)
    service_worker_path = (
        os.path.dirname(__file__) + os.sep + "pwa_service_files" + os.sep + "sw.js"
    )

    # dumps our webmanifest
    manifest["name"] = config["pwa_name"]
    manifest["short_name"] = app.config.project
    manifest["short_name"] = config["pwa_short_name"]
    manifest["theme_color"] = config["pwa_theme_color"]
    manifest["background_color"] = config["pwa_background_color"]
    manifest["display"] = config["pwa_display"]

    cache_name = "sphinx-app-" + random.randrange(10000, 99999)

    # code gen our cache name
    with open(service_worker_path, "wt") as f:
        for line in f:
            f.write(line.replace("/* CODE-GEN CACHENAME */", cache_name))

    # icons is a required manifest attribute
    if config["pwa_icons"] is None:
        logger.error("Icons is required to be configured!")
    else:
        icons = []
 
        for icon in config["icons"]:
            if ".png" in icon[0]:
                icons.append(
                    {
                        "src": icon[0],
                        "type": "image/png",
                        "sizes": icon[1]
                    }
                )
            elif ".jpg" in icon[0] or ".jpeg" in icon[0]:
                icons.append(
                    {
                        "src": icon[0],
                        "type": "image/jpeg",
                        "sizes": icon[1]
                    }
                )
            elif ".svg" in icon[0]:
                icons.append(
                    {
                        "src": icon[0],
                        "type": "image/svg+xml",
                        "sizes": icon[1]
                    }
                )
            else:
                logger.error ("Specified image is unrecognized type:", icon[0])

        manifest["icons"] = icons

    # dumps our manifest
    with open(outDirStatic + "app.webmanifest", "w") as f:
        json.dump(manifest, f)

    # dumps a json file with our cache
    with open(outDirStatic + "cache.json", "w") as f:
        json.dump(files_to_cache, f)

    # copies over our service worker
    shutil.copyfile(
        service_worker_path,
        outDir + os.sep + "sw.js",
    )


def html_page_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: Dict[str, Any],
    doctree: nodes.document,
) -> None:
    if pagename == "index":
        context[
            "metatags"
        ] += '<script>"serviceWorker"in navigator&&navigator.serviceWorker.register("sw.js").catch((e) => window.alert(e));</script>'
        context["metatags"] += f'<link rel="manifest" href="_static/app.webmanifest"/>'

        if app.config["pwa_apple_icon"] is not None:
            context[
                "metatags"
            ] += f'<link rel="apple-touch-icon" href="{app.config["pwa_apple_icon"]}">'


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_config_value("pwa_name", app.config.project, "html")
    app.add_config_value("pwa_short_name", app.config.project, "html")
    app.add_config_value("pwa_theme_color", "", "html")
    app.add_config_value("pwa_background_color", "", "html")
    app.add_config_value("pwa_display", "standalone", "html")
    app.add_config_value("pwa_icons", None, "html")
    app.add_config_value("pwa_apple_icon", "", "html")

    app.connect("html-page-context", html_page_context)
    app.connect("build-finished", build_finished)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
