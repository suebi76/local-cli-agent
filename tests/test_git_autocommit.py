"""Tests for git auto-commit feature in executor.py."""
import subprocess
import local_cli_agent.executor as executor_module


def test_git_autocommit_skips_if_disabled(monkeypatch):
    """_git_autocommit does nothing when git_autocommit setting is False."""
    calls = []
    monkeypatch.setattr(
        "local_cli_agent.executor.subprocess.run",
        lambda *a, **kw: calls.append(a) or type("R", (), {"returncode": 0})(),
    )
    # Patch settings to return False
    import local_cli_agent.settings as _settings
    monkeypatch.setattr(_settings, "get", lambda key: False)
    executor_module._git_autocommit("/some/file.py", "write")
    assert calls == [], "subprocess.run should not be called when disabled"


def test_git_autocommit_skips_if_no_git_repo(monkeypatch, tmp_path):
    """_git_autocommit does nothing when not inside a git repo."""
    import local_cli_agent.settings as _settings
    monkeypatch.setattr(_settings, "get", lambda key: True)

    # First subprocess.run call (git rev-parse) returns non-zero
    call_log = []

    def fake_run(cmd, *args, **kwargs):
        call_log.append(cmd)
        return type("R", (), {"returncode": 1, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(executor_module.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)
    executor_module._git_autocommit(str(tmp_path / "file.py"), "write")
    # Only the rev-parse check should have run, no commit
    assert len(call_log) == 1
    assert "rev-parse" in call_log[0]


def test_git_autocommit_runs_commit_when_enabled(monkeypatch, tmp_path):
    """_git_autocommit calls git add + git commit when enabled and in a repo."""
    import local_cli_agent.settings as _settings
    monkeypatch.setattr(_settings, "get", lambda key: True)

    call_log = []

    def fake_run(cmd, *args, **kwargs):
        call_log.append(cmd)
        return type("R", (), {"returncode": 0, "stdout": "1 file changed", "stderr": ""})()

    monkeypatch.setattr(executor_module.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)
    executor_module._git_autocommit(str(tmp_path / "hello.py"), "write")

    assert any("rev-parse" in c for c in call_log), "Should check git repo"
    assert any("git add" in c for c in call_log), "Should stage the file"
    assert any("git commit" in c for c in call_log), "Should create a commit"
    assert any("agent: write" in c for c in call_log), "Commit message should include action"
