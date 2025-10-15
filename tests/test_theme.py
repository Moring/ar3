from pathlib import Path

import pytest
from django.template.loader import get_template


@pytest.mark.story("S-003")
def test_base_layout_blocks_exist():
    tpl = get_template("ui/base.html")
    content = tpl.render()
    assert "Inspinia" in content


@pytest.mark.story("S-003")
def test_theme_assets_moved_and_theme_folder_removed():
    assert not Path("theme").exists()
    assert Path("ui/static/ui/css/app.min.css").exists()
    assert Path("ui/static/ui/js/app.js").exists()
