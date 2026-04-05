import os
import local_cli_agent.config as config_module
import local_cli_agent.constants as const_module


def test_save_and_load_last_model(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    monkeypatch.setattr(config_module, "ENV_FILE", str(env_file))
    monkeypatch.delenv("LOCAL_CLI_LAST_MODEL", raising=False)
    config_module.save_last_model("ollama:llama3.2:3b")
    assert config_module.load_last_model() == "ollama:llama3.2:3b"


def test_load_last_model_from_env_var(monkeypatch):
    monkeypatch.setenv("LOCAL_CLI_LAST_MODEL", "lmstudio:my-model")
    assert config_module.load_last_model() == "lmstudio:my-model"


def test_load_last_model_returns_none_if_missing(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    monkeypatch.setattr(config_module, "ENV_FILE", str(env_file))
    monkeypatch.delenv("LOCAL_CLI_LAST_MODEL", raising=False)
    assert config_module.load_last_model() is None


def test_build_system_prompt_contains_version():
    prompt = config_module.build_system_prompt()
    assert const_module.VERSION in prompt


def test_build_system_prompt_with_extra():
    prompt = config_module.build_system_prompt(extra="be extra helpful")
    assert "be extra helpful" in prompt


def test_build_system_prompt_contains_cwd():
    prompt = config_module.build_system_prompt()
    assert os.getcwd() in prompt
