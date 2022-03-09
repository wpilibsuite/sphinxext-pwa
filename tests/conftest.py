import pytest
from bs4 import BeautifulSoup
from sphinx.testing.path import path

from sphinx.application import Sphinx


pytest_plugins = "sphinx.testing.fixtures"


@pytest.fixture(scope="session")
def rootdir():
    return path(__file__).parent.abspath() / "roots"


@pytest.fixture()
def content(app):
    app.build()
    yield app


def _meta_tags(content, subdir=None):
    if subdir is None:
        c = (content.outdir / "index.html").read_text()
    else:
        c = (content.outdir / subdir / "index.html").read_text()
    return BeautifulSoup(c, "html.parser").find_all("meta")


@pytest.fixture()
def meta_tags(content):
    return _meta_tags(content)


def pytest_configure(config):
    config.addinivalue_line("markers", "sphinx")
