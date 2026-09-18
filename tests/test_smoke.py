from PIL import Image
from app.smoke import create_source, SOURCE


def test_fictional_source_is_safe_and_readable(tmp_path):
    path = tmp_path / "source.png"
    create_source(path)
    assert Image.open(path).size == (1600, 2200)
    assert "fictional" in SOURCE.casefold()
    assert "never administer" in SOURCE.casefold()
    assert "no dose" in SOURCE.casefold()
