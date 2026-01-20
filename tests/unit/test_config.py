import pytest
import json
from pathlib import Path

from config import ConfigManager


@pytest.fixture
def config_manager(mock_config_file):
    config_file, profiles_dir = mock_config_file
    
    class MockConfigManager(ConfigManager):
        CONFIG_DIR = config_file.parent
        CONFIG_FILE = config_file
        PROFILES_DIR = profiles_dir
        TVSERVER_CONFIG_FILE = Path("/tmp/mock_tvserver_config.json")
    
    return MockConfigManager()


@pytest.mark.asyncio
async def test_initialize_creates_directories(config_manager):
    await config_manager.initialize()
    
    assert config_manager.CONFIG_DIR.exists()
    assert config_manager.PROFILES_DIR.exists()


@pytest.mark.asyncio
async def test_initialize_creates_default_config(config_manager):
    await config_manager.initialize()
    
    assert "basic" in config_manager.config
    assert "hostname" in config_manager.config["basic"]
    assert config_manager.config["basic"]["hostname"] == "streambox"


@pytest.mark.asyncio
async def test_get_config_value(config_manager):
    await config_manager.initialize()
    
    hostname = config_manager.get("basic.hostname")
    assert hostname == "streambox"


@pytest.mark.asyncio
async def test_set_config_value(config_manager):
    await config_manager.initialize()
    
    config_manager.set("basic.hostname", "test-hostname")
    hostname = config_manager.get("basic.hostname")
    assert hostname == "test-hostname"


@pytest.mark.asyncio
async def test_save_config(config_manager):
    await config_manager.initialize()
    config_manager.set("basic.hostname", "saved-hostname")
    await config_manager.save()
    
    with open(config_manager.CONFIG_FILE, "r") as f:
        saved_config = json.load(f)
    
    assert saved_config["basic"]["hostname"] == "saved-hostname"


@pytest.mark.asyncio
async def test_export_config(config_manager):
    await config_manager.initialize()
    
    profile = await config_manager.export_config("test-profile")
    
    assert profile["name"] == "test-profile"
    assert "config" in profile


@pytest.mark.asyncio
async def test_save_and_load_profile(config_manager):
    await config_manager.initialize()
    config_manager.set("basic.hostname", "profile-hostname")
    
    save_success = await config_manager.save_profile("test-profile")
    assert save_success is True
    
    config_manager.set("basic.hostname", "other-hostname")
    load_success = await config_manager.load_profile("test-profile")
    assert load_success is True
    
    assert config_manager.get("basic.hostname") == "profile-hostname"


@pytest.mark.asyncio
async def test_list_profiles(config_manager):
    await config_manager.initialize()
    
    await config_manager.save_profile("profile1")
    await config_manager.save_profile("profile2")
    
    profiles = await config_manager.list_profiles()
    
    assert "profile1" in profiles
    assert "profile2" in profiles


@pytest.mark.asyncio
async def test_delete_profile(config_manager):
    await config_manager.initialize()
    
    await config_manager.save_profile("to-delete")
    profiles_before = await config_manager.list_profiles()
    assert "to-delete" in profiles_before
    
    delete_success = await config_manager.delete_profile("to-delete")
    assert delete_success is True
    
    profiles_after = await config_manager.list_profiles()
    assert "to-delete" not in profiles_after
