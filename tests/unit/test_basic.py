import pytest
from unittest.mock import patch, MagicMock
from basic import BasicSettingsManager


@pytest.fixture
def basic_manager():
    return BasicSettingsManager()


@pytest.mark.asyncio
async def test_validate_hostname_valid(basic_manager):
    assert basic_manager._validate_hostname("valid-hostname") is True
    assert basic_manager._validate_hostname("valid.hostname") is True
    assert basic_manager._validate_hostname("Valid-123.Hostname") is True


@pytest.mark.asyncio
async def test_validate_hostname_invalid(basic_manager):
    assert basic_manager._validate_hostname("") is False
    assert basic_manager._validate_hostname("-invalid") is False
    assert basic_manager._validate_hostname("invalid-") is False
    assert basic_manager._validate_hostname("invalid hostname") is False
    assert basic_manager._validate_hostname("a" * 254) is False


@pytest.mark.asyncio
async def test_get_hostname(basic_manager):
    with patch.object(basic_manager, '_run_command', return_value=(True, "test-hostname")):
        hostname = await basic_manager.get_hostname()
        assert hostname == "test-hostname"


@pytest.mark.asyncio
async def test_get_hostname_default(basic_manager):
    with patch.object(basic_manager, '_run_command', return_value=(False, "")):
        hostname = await basic_manager.get_hostname()
        assert hostname == "streambox"


@pytest.mark.asyncio
async def test_set_hostname_valid(basic_manager):
    with patch.object(basic_manager, '_run_command', return_value=(True, "")):
        success = await basic_manager.set_hostname("new-hostname")
        assert success is True


@pytest.mark.asyncio
async def test_set_hostname_invalid(basic_manager):
    success = await basic_manager.set_hostname("")
    assert success is False


@pytest.mark.asyncio
async def test_get_timezone(basic_manager):
    with patch.object(basic_manager, '_run_command', return_value=(True, "America/New_York")):
        timezone = await basic_manager.get_timezone()
        assert timezone == "America/New_York"


@pytest.mark.asyncio
async def test_get_timezone_default(basic_manager):
    with patch.object(basic_manager, '_run_command', return_value=(False, "")):
        timezone = await basic_manager.get_timezone()
        assert timezone == "UTC"


@pytest.mark.asyncio
async def test_set_timezone_valid(basic_manager):
    with patch.object(basic_manager, 'get_available_timezones', return_value=["UTC", "America/New_York"]):
        with patch.object(basic_manager, '_run_command', return_value=(True, "")):
            success = await basic_manager.set_timezone("America/New_York")
            assert success is True


@pytest.mark.asyncio
async def test_set_timezone_invalid(basic_manager):
    with patch.object(basic_manager, 'get_available_timezones', return_value=["UTC"]):
        success = await basic_manager.set_timezone("Invalid/Timezone")
        assert success is False


@pytest.mark.asyncio
async def test_get_locale(basic_manager):
    with patch.object(basic_manager, '_run_command', return_value=(True, "LANG=en_US.UTF-8\nLC_CTYPE=\"en_US.UTF-8\"")):
        locale = await basic_manager.get_locale()
        assert locale == "en_US.UTF-8"


@pytest.mark.asyncio
async def test_get_locale_default(basic_manager):
    with patch.object(basic_manager, '_run_command', return_value=(False, "")):
        locale = await basic_manager.get_locale()
        assert locale == "en_US.UTF-8"


@pytest.mark.asyncio
async def test_set_locale_valid(basic_manager):
    with patch.object(basic_manager, 'get_available_locales', return_value=["en_US.utf8", "zh_CN.utf8"]):
        with patch.object(basic_manager, '_run_command', return_value=(True, "")):
            success = await basic_manager.set_locale("en_US.utf8")
            assert success is True


@pytest.mark.asyncio
async def test_set_locale_invalid(basic_manager):
    with patch.object(basic_manager, 'get_available_locales', return_value=["en_US.utf8"]):
        success = await basic_manager.set_locale("invalid_locale")
        assert success is False


@pytest.mark.asyncio
async def test_get_ntp_server(basic_manager):
    with patch.object(basic_manager, '_run_command', return_value=(True, "yes")):
        ntp_server = await basic_manager.get_ntp_server()
        assert ntp_server == "yes"


@pytest.mark.asyncio
async def test_get_ntp_server_default(basic_manager):
    with patch.object(basic_manager, '_run_command', return_value=(False, "")):
        ntp_server = await basic_manager.get_ntp_server()
        assert ntp_server == "yes"


@pytest.mark.asyncio
async def test_set_ntp_server_enable(basic_manager):
    with patch.object(basic_manager, '_run_command', return_value=(True, "")):
        success = await basic_manager.set_ntp_server("yes")
        assert success is True


@pytest.mark.asyncio
async def test_set_ntp_server_disable(basic_manager):
    with patch.object(basic_manager, '_run_command', return_value=(True, "")):
        success = await basic_manager.set_ntp_server("no")
        assert success is True


@pytest.mark.asyncio
async def test_get_basic_settings(basic_manager):
    with patch.object(basic_manager, 'get_hostname', return_value="test-host"):
        with patch.object(basic_manager, 'get_timezone', return_value="UTC"):
            with patch.object(basic_manager, 'get_locale', return_value="en_US.UTF-8"):
                with patch.object(basic_manager, 'get_ntp_server', return_value="yes"):
                    settings = await basic_manager.get_basic_settings()
                    
                    assert settings["hostname"] == "test-host"
                    assert settings["timezone"] == "UTC"
                    assert settings["locale"] == "en_US.UTF-8"
                    assert settings["ntp_server"] == "yes"


@pytest.mark.asyncio
async def test_set_basic_settings(basic_manager):
    settings = {
        "hostname": "new-host",
        "timezone": "America/New_York",
        "locale": "en_US.utf8",
        "ntp_server": "yes"
    }
    
    with patch.object(basic_manager, 'set_hostname', return_value=True):
        with patch.object(basic_manager, 'set_timezone', return_value=True):
            with patch.object(basic_manager, 'set_locale', return_value=True):
                with patch.object(basic_manager, 'set_ntp_server', return_value=True):
                    success = await basic_manager.set_basic_settings(settings)
                    assert success is True
