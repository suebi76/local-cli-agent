"""Tests for Markdown rendering module."""
import local_cli_agent.rendering as rendering


def test_render_does_not_crash_on_plain_text(capsys):
    """render() handles plain text without errors."""
    rendering.render("Hello, world!")
    # No exception = pass


def test_render_does_not_crash_on_code_block(capsys):
    """render() handles code blocks without errors."""
    rendering.render("```python\ndef foo():\n    return 42\n```")
    # No exception = pass


def test_render_does_not_crash_on_empty_string(capsys):
    """render('') returns immediately without output or crash."""
    rendering.render("")
    out = capsys.readouterr().out
    assert out == ""


def test_render_fallback_when_rich_unavailable(monkeypatch, capsys):
    """render() falls back to plain print when rich is not available."""
    monkeypatch.setattr(rendering, "_available", False)
    rendering.render("fallback text")
    out = capsys.readouterr().out
    assert "fallback text" in out


def test_is_available_returns_bool():
    """is_available() always returns a bool."""
    result = rendering.is_available()
    assert isinstance(result, bool)
