import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config_file(tmp_path):
    config_dir = tmp_path / "streambox-settings"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    
    profiles_dir = config_dir / "profiles"
    profiles_dir.mkdir()
    
    return config_file, profiles_dir
