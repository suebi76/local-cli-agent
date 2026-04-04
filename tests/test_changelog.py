import json
import local_cli_agent.changelog as cl_module


def test_get_changelog_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(cl_module, "CHANGELOG", str(tmp_path / "changelog.json"))
    result = cl_module.get_changelog()
    assert "No changelog entries yet" in result


def test_add_and_get_entry(tmp_path, monkeypatch):
    path = str(tmp_path / "changelog.json")
    monkeypatch.setattr(cl_module, "CHANGELOG", path)
    cl_module.add_changelog_entry("Test change")
    result = cl_module.get_changelog()
    assert "Test change" in result


def test_multiple_entries(tmp_path, monkeypatch):
    path = str(tmp_path / "changelog.json")
    monkeypatch.setattr(cl_module, "CHANGELOG", path)
    cl_module.add_changelog_entry("First")
    cl_module.add_changelog_entry("Second")
    cl_module.add_changelog_entry("Third")
    result = cl_module.get_changelog()
    assert "First" in result
    assert "Second" in result
    assert "Third" in result


def test_entry_contains_version(tmp_path, monkeypatch):
    path = str(tmp_path / "changelog.json")
    monkeypatch.setattr(cl_module, "CHANGELOG", path)
    cl_module.add_changelog_entry("versioned change")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert "version" in data[0]
    assert "date" in data[0]


def test_max_20_entries_shown(tmp_path, monkeypatch):
    path = str(tmp_path / "changelog.json")
    monkeypatch.setattr(cl_module, "CHANGELOG", path)
    for i in range(25):
        cl_module.add_changelog_entry(f"entry {i}")
    result = cl_module.get_changelog()
    lines = [l for l in result.strip().split("\n") if l.strip()]
    assert len(lines) <= 20
