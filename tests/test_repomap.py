"""Tests for the repository map module."""
import os
import local_cli_agent.repomap as repomap
import local_cli_agent.settings as _settings


def test_get_repo_map_empty_dir(tmp_path, monkeypatch):
    """Returns '' for a directory that has no project markers."""
    monkeypatch.setattr(_settings, "get", lambda key: True)
    result = repomap.get_repo_map(str(tmp_path))
    assert result == ""


def test_get_repo_map_disabled(tmp_path, monkeypatch):
    """Returns '' when repo_map setting is False."""
    monkeypatch.setattr(_settings, "get", lambda key: False)
    result = repomap.get_repo_map(str(tmp_path))
    assert result == ""


def test_get_repo_map_detects_classes_and_functions(tmp_path, monkeypatch):
    """Extracts class names and function names from a Python file."""
    monkeypatch.setattr(_settings, "get", lambda key: True)

    # Create a fake project root marker
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

    # Create a Python file with a class and function
    py_file = tmp_path / "mymodule.py"
    py_file.write_text(
        "class Foo:\n"
        "    def bar(self): pass\n"
        "    def baz(self): pass\n"
        "\n"
        "def standalone(): pass\n"
    )

    result = repomap.get_repo_map(str(tmp_path))
    assert "class Foo:" in result
    assert "def bar()" in result
    assert "def baz()" in result
    assert "def standalone()" in result
    assert "REPO-MAP" in result


def test_get_repo_map_skips_venv(tmp_path, monkeypatch):
    """Files inside .venv/ or venv/ are not included."""
    monkeypatch.setattr(_settings, "get", lambda key: True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

    # Put a file inside venv — should be skipped
    venv_dir = tmp_path / "venv" / "lib"
    venv_dir.mkdir(parents=True)
    (venv_dir / "ignored.py").write_text("def secret(): pass\n")

    # Real file outside venv
    (tmp_path / "main.py").write_text("def real_func(): pass\n")

    result = repomap.get_repo_map(str(tmp_path))
    assert "real_func" in result
    assert "secret" not in result


def test_get_repo_map_handles_syntax_error_gracefully(tmp_path, monkeypatch):
    """Files with syntax errors are silently skipped."""
    monkeypatch.setattr(_settings, "get", lambda key: True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    (tmp_path / "broken.py").write_text("def (: pass\n")  # invalid syntax
    (tmp_path / "good.py").write_text("def works(): pass\n")

    result = repomap.get_repo_map(str(tmp_path))
    # Should not crash, and good.py should still appear
    assert "works" in result


def test_parse_python_empty_file(tmp_path):
    """_parse_python returns [] for an empty file."""
    f = tmp_path / "empty.py"
    f.write_text("")
    assert repomap._parse_python(str(f)) == []


def test_parse_python_no_symbols(tmp_path):
    """_parse_python returns [] for a file with only assignments."""
    f = tmp_path / "consts.py"
    f.write_text("X = 1\nY = 'hello'\n")
    assert repomap._parse_python(str(f)) == []
