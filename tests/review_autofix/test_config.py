import pytest

from ugh_quantamental.review_autofix.config import _parse_csv, load_config


@pytest.mark.parametrize("token", ["1", "true", "TRUE", "yes", "on"])
def test_load_config_accepts_true_tokens_for_dry_run(monkeypatch, token: str) -> None:
    monkeypatch.setenv("DRY_RUN", token)
    config = load_config()
    assert config.dry_run is True


@pytest.mark.parametrize("token", ["0", "false", "FALSE", "no", "off"])
def test_load_config_accepts_false_tokens_for_dry_run(monkeypatch, token: str) -> None:
    monkeypatch.setenv("DRY_RUN", token)
    config = load_config()
    assert config.dry_run is False


def test_load_config_rejects_invalid_boolean_for_dry_run(monkeypatch) -> None:
    monkeypatch.setenv("DRY_RUN", "maybe")
    with pytest.raises(ValueError, match=r"invalid boolean env DRY_RUN"):
        load_config()


def test_parse_csv_empty_string_uses_default(monkeypatch) -> None:
    """_parse_csv treats an empty env var as unset and falls back to the default."""
    monkeypatch.setenv("ALLOWED_BOT_REVIEWERS", "")
    result = _parse_csv("ALLOWED_BOT_REVIEWERS", "chatgpt-codex-connector[bot]")
    assert result == ("chatgpt-codex-connector[bot]",)


def test_parse_csv_unset_uses_default(monkeypatch) -> None:
    """_parse_csv uses the default when the env var is not present at all."""
    monkeypatch.delenv("ALLOWED_BOT_REVIEWERS", raising=False)
    result = _parse_csv("ALLOWED_BOT_REVIEWERS", "chatgpt-codex-connector[bot]")
    assert result == ("chatgpt-codex-connector[bot]",)


def test_parse_csv_whitespace_only_uses_default(monkeypatch) -> None:
    """_parse_csv treats a whitespace-only env var the same as empty."""
    monkeypatch.setenv("ALLOWED_BOT_REVIEWERS", "   ")
    result = _parse_csv("ALLOWED_BOT_REVIEWERS", "chatgpt-codex-connector[bot]")
    assert result == ("chatgpt-codex-connector[bot]",)


def test_parse_csv_explicit_value_overrides_default(monkeypatch) -> None:
    """When env var is set to a non-empty value it wins over the default."""
    monkeypatch.setenv("ALLOWED_BOT_REVIEWERS", "other-bot[bot]")
    result = _parse_csv("ALLOWED_BOT_REVIEWERS", "chatgpt-codex-connector[bot]")
    assert result == ("other-bot[bot]",)


def test_load_config_allowed_bot_reviewers_default(monkeypatch) -> None:
    """load_config returns chatgpt-codex-connector[bot] when ALLOWED_BOT_REVIEWERS is unset."""
    monkeypatch.delenv("ALLOWED_BOT_REVIEWERS", raising=False)
    config = load_config()
    assert "chatgpt-codex-connector[bot]" in config.allowed_bot_reviewers


def test_load_config_allowed_bot_reviewers_empty_string_uses_default(monkeypatch) -> None:
    """load_config returns chatgpt-codex-connector[bot] when ALLOWED_BOT_REVIEWERS=''."""
    monkeypatch.setenv("ALLOWED_BOT_REVIEWERS", "")
    config = load_config()
    assert "chatgpt-codex-connector[bot]" in config.allowed_bot_reviewers
