import pytest
from sphinx.application import Sphinx
import conftest
import os


@pytest.mark.sphinx("html", testroot="manifest-generation")
def test_manifest_generation(content):
    assert True
