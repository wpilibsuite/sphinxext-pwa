import pytest
from sphinx.application import Sphinx
from bs4 import BeautifulSoup
from bs4 import element
import json

manifest = """{"name": "Python", "short_name": "Python", "theme_color": "", "background_color": "", "display": "standalone", "scope": "../", "start_url": "../index.html?pwa", "icons": [{"src": "_static/test-icon.png", "type": "image/png", "sizes": "120x120"}]}"""


@pytest.mark.sphinx("html", testroot="manifest-generation")
def test_manifest_linking(get_link_tags):

    valid = False

    for item in get_link_tags:
        manifest_tag = item.get("rel")
        manifest_location = item.get("href")

        if "manifest" in manifest_tag and "app.webmanifest" in manifest_location:
            valid = True

    assert valid


@pytest.mark.sphinx("html", testroot="manifest-generation")
def test_manifest_generated(content):
    file = (content.outdir / "app.webmanifest").read_text()

    if file is None:
        assert False

    if manifest not in file:
        assert False

    assert True


@pytest.mark.sphinx("html", testroot="manifest-generation")
def test_serviceworker_generated(content):
    file = (content.outdir / "sw.js").read_text()

    if file is None:
        assert False

    assert True
