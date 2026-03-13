from pathlib import Path

from ugh_quantamental.review_autofix.state_store import FileStateStore


def test_file_state_store_marks_and_detects_keys(tmp_path: Path) -> None:
    store = FileStateStore(str(tmp_path / "state.json"))
    key = "review_comment:1:abc"
    assert store.seen(key) is False
    store.mark(key)
    assert store.seen(key) is True
