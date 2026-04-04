import os
import local_cli_agent.config as config_module
import local_cli_agent.constants as const_module


def test_load_api_key_no_env_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "ENV_FILE", str(tmp_path / ".env"))
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    assert config_module.load_api_key() is None


def test_load_api_key_from_env_var(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key-123")
    assert config_module.load_api_key() == "test-key-123"


def test_load_api_key_from_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("NVIDIA_API_KEY=file-key-456\n", encoding="utf-8")
    monkeypatch.setattr(config_module, "ENV_FILE", str(env_file))
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    assert config_module.load_api_key() == "file-key-456"


def test_env_var_takes_priority_over_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("NVIDIA_API_KEY=file-key\n", encoding="utf-8")
    monkeypatch.setattr(config_module, "ENV_FILE", str(env_file))
    monkeypatch.setenv("NVIDIA_API_KEY", "env-key")
    assert config_module.load_api_key() == "env-key"


def test_load_api_key_strips_quotes(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text('NVIDIA_API_KEY="quoted-key"\n', encoding="utf-8")
    monkeypatch.setattr(config_module, "ENV_FILE", str(env_file))
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    assert config_module.load_api_key() == "quoted-key"


def test_build_system_prompt_contains_version():
    prompt = config_module.build_system_prompt()
    assert const_module.VERSION in prompt


def test_build_system_prompt_with_extra():
    prompt = config_module.build_system_prompt(extra="be extra helpful")
    assert "be extra helpful" in prompt


def test_build_system_prompt_contains_cwd():
    prompt = config_module.build_system_prompt()
    assert os.getcwd() in prompt
