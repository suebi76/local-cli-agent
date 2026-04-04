import local_cli_agent.executor as executor_module


def test_unknown_tool_returns_error():
    result = executor_module.execute_tool("nonexistent_tool", {})
    assert "Unknown tool" in result


def test_invalid_json_arguments():
    result = executor_module.execute_tool("bash", "not valid json {{")
    assert "Error" in result


def test_read_file_not_found(tmp_path):
    result = executor_module.execute_tool("read_file", {"path": str(tmp_path / "ghost.txt")})
    assert "Error" in result or "not found" in result.lower()


def test_list_directory(tmp_path):
    (tmp_path / "file.txt").write_text("hello")
    result = executor_module.execute_tool("list_directory", {"path": str(tmp_path)})
    assert "file.txt" in result


def test_auto_approve_skips_prompt(monkeypatch):
    monkeypatch.setattr(executor_module, "auto_approve", True)
    # ask_permission should return True without any input
    result = executor_module.ask_permission("test_tool", "some details")
    assert result is True
    monkeypatch.setattr(executor_module, "auto_approve", False)


def test_read_file_success(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("world", encoding="utf-8")
    result = executor_module.execute_tool("read_file", {"path": str(f)})
    assert "world" in result


def test_list_directory_not_found(tmp_path):
    result = executor_module.execute_tool("list_directory", {"path": str(tmp_path / "nope")})
    assert "Error" in result or "Not found" in result


def test_glob_find_no_match(tmp_path):
    result = executor_module.execute_tool("glob_find", {"pattern": "*.xyz", "path": str(tmp_path)})
    assert "No files found" in result


def test_grep_search_no_match(tmp_path):
    (tmp_path / "file.txt").write_text("hello world")
    result = executor_module.execute_tool("grep_search", {"pattern": "zzznomatch", "path": str(tmp_path)})
    assert "No matches" in result
