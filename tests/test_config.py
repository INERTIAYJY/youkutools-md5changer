from pathlib import Path

from md5_rebuilder.utils.config import SettingsStore


def test_settings_store_does_not_persist_output_dir(tmp_path: Path):
    store = SettingsStore(tmp_path / "settings.json")

    store.save({"output_dir": "D:/old/path", "suffix": "fresh"})
    reloaded = SettingsStore(tmp_path / "settings.json")

    assert "output_dir" not in reloaded.data
    assert reloaded.data["suffix"] == "fresh"


def test_settings_store_persists_audio_choice(tmp_path: Path):
    store = SettingsStore(tmp_path / "settings.json")

    store.save({"include_audio": False})
    reloaded = SettingsStore(tmp_path / "settings.json")

    assert reloaded.data["include_audio"] is False


def test_settings_store_persists_theme_choice(tmp_path: Path):
    store = SettingsStore(tmp_path / "settings.json")

    store.save({"theme": "light"})
    reloaded = SettingsStore(tmp_path / "settings.json")

    assert reloaded.data["theme"] == "light"
