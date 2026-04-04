from local_cli_agent.web import HTMLStripper, strip_html


def test_strip_html_basic():
    assert strip_html("<b>hello</b>") == "hello"


def test_strip_html_removes_script():
    result = strip_html("<html><script>alert(1)</script><p>content</p></html>")
    assert "alert" not in result
    assert "content" in result


def test_strip_html_removes_style():
    result = strip_html("<style>body{color:red}</style><p>text</p>")
    assert "color" not in result
    assert "text" in result


def test_strip_html_collapses_newlines():
    result = strip_html("<p>line1</p><p>line2</p>")
    # Should not have more than 2 consecutive newlines
    assert "\n\n\n" not in result


def test_strip_html_empty_input():
    result = strip_html("")
    assert result == ""


def test_strip_html_malformed():
    # Should not raise, should return something
    result = strip_html("<p unclosed <b>text</b>")
    assert isinstance(result, str)


def test_strip_html_nested_skip_tags():
    html = "<nav><div><script>bad</script></div></nav><p>good</p>"
    result = strip_html(html)
    assert "bad" not in result
    assert "good" in result


def test_htmlstripper_get_text():
    stripper = HTMLStripper()
    stripper.feed("<p>Hello <b>World</b></p>")
    text = stripper.get_text()
    assert "Hello" in text
    assert "World" in text


def test_htmlstripper_empty():
    stripper = HTMLStripper()
    stripper.feed("")
    assert stripper.get_text() == ""
