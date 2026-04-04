import json
import local_cli_agent.memory as mem_module


def test_load_memory_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(mem_module, "MEMORY_FILE", str(tmp_path / "memory.json"))
    assert mem_module.load_memory() == {}


def test_load_memory_invalid_json(tmp_path, monkeypatch):
    path = tmp_path / "memory.json"
    path.write_text("not json", encoding="utf-8")
    monkeypatch.setattr(mem_module, "MEMORY_FILE", str(path))
    assert mem_module.load_memory() == {}


def test_memory_roundtrip(tmp_path, monkeypatch):
    path = str(tmp_path / "memory.json")
    monkeypatch.setattr(mem_module, "MEMORY_FILE", path)
    data = {"key1": {"content": "hello", "saved_at": "2024-01-01"}}
    mem_module.save_memory_file(data)
    loaded = mem_module.load_memory()
    assert loaded == data


def test_memory_unicode(tmp_path, monkeypatch):
    path = str(tmp_path / "memory.json")
    monkeypatch.setattr(mem_module, "MEMORY_FILE", path)
    data = {"key": {"content": "Héllo Wörld", "saved_at": "2024-01-01"}}
    mem_module.save_memory_file(data)
    loaded = mem_module.load_memory()
    assert loaded["key"]["content"] == "Héllo Wörld"


def test_save_creates_valid_json(tmp_path, monkeypatch):
    path = str(tmp_path / "memory.json")
    monkeypatch.setattr(mem_module, "MEMORY_FILE", path)
    mem_module.save_memory_file({"a": {"content": "test", "saved_at": "x"}})
    with open(path, encoding="utf-8") as f:
        parsed = json.load(f)
    assert "a" in parsed
