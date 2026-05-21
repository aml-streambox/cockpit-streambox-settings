import pytest

from applications import ApplicationManager


@pytest.fixture
def application_manager():
    return ApplicationManager()


def command_key(args):
    return tuple(args)


@pytest.mark.asyncio
async def test_get_status_prefers_active_application(application_manager):
    responses = {
        command_key(["systemctl", "show", "--property=LoadState", "--value", "gst-manager.service"]): (True, "loaded"),
        command_key(["systemctl", "is-active", "--quiet", "gst-manager.service"]): (True, ""),
        command_key(["systemctl", "is-enabled", "--quiet", "gst-manager.service"]): (True, ""),
        command_key(["systemctl", "show", "--property=LoadState", "--value", "one-kvm.service"]): (True, "loaded"),
        command_key(["systemctl", "is-active", "--quiet", "one-kvm.service"]): (False, ""),
        command_key(["systemctl", "is-enabled", "--quiet", "one-kvm.service"]): (False, ""),
        command_key(["systemctl", "show", "--property=LoadState", "--value", "sbs-server.service"]): (True, "loaded"),
        command_key(["systemctl", "is-active", "--quiet", "sbs-server.service"]): (False, ""),
        command_key(["systemctl", "is-enabled", "--quiet", "sbs-server.service"]): (False, ""),
        command_key(["systemctl", "show", "--property=LoadState", "--value", "sbs-webui.service"]): (True, "loaded"),
        command_key(["systemctl", "is-active", "--quiet", "sbs-webui.service"]): (False, ""),
        command_key(["systemctl", "is-enabled", "--quiet", "sbs-webui.service"]): (False, ""),
    }

    application_manager._run_command = lambda args, timeout=30: responses[command_key(args)]

    status = await application_manager.get_status()

    assert status["active_application"] == "gst-manager"
    assert status["default_application"] == "gst-manager"
    assert status["conflict"] is False


@pytest.mark.asyncio
async def test_get_status_reports_conflict(application_manager):
    responses = {
        command_key(["systemctl", "show", "--property=LoadState", "--value", "gst-manager.service"]): (True, "loaded"),
        command_key(["systemctl", "is-active", "--quiet", "gst-manager.service"]): (True, ""),
        command_key(["systemctl", "is-enabled", "--quiet", "gst-manager.service"]): (True, ""),
        command_key(["systemctl", "show", "--property=LoadState", "--value", "one-kvm.service"]): (True, "loaded"),
        command_key(["systemctl", "is-active", "--quiet", "one-kvm.service"]): (True, ""),
        command_key(["systemctl", "is-enabled", "--quiet", "one-kvm.service"]): (True, ""),
        command_key(["systemctl", "show", "--property=LoadState", "--value", "sbs-server.service"]): (True, "loaded"),
        command_key(["systemctl", "is-active", "--quiet", "sbs-server.service"]): (False, ""),
        command_key(["systemctl", "is-enabled", "--quiet", "sbs-server.service"]): (False, ""),
        command_key(["systemctl", "show", "--property=LoadState", "--value", "sbs-webui.service"]): (True, "loaded"),
        command_key(["systemctl", "is-active", "--quiet", "sbs-webui.service"]): (False, ""),
        command_key(["systemctl", "is-enabled", "--quiet", "sbs-webui.service"]): (False, ""),
    }

    application_manager._run_command = lambda args, timeout=30: responses[command_key(args)]

    status = await application_manager.get_status()

    assert status["active_application"] == "gst-manager"
    assert status["conflict"] is True


@pytest.mark.asyncio
async def test_set_active_application_switches_services_in_order(application_manager):
    calls = []

    def run_command(args, timeout=30):
        calls.append(args)
        if args[:4] == ["systemctl", "show", "--property=LoadState", "--value"]:
            return True, "loaded"
        return True, ""

    application_manager._run_command = run_command

    success = await application_manager.set_active_application("one-kvm")

    assert success is True
    assert calls == [
        ["systemctl", "show", "--property=LoadState", "--value", "one-kvm.service"],
        ["systemctl", "show", "--property=LoadState", "--value", "gst-manager.service"],
        ["systemctl", "disable", "gst-manager.service"],
        ["systemctl", "stop", "gst-manager.service"],
        ["systemctl", "show", "--property=LoadState", "--value", "sbs-server.service"],
        ["systemctl", "disable", "sbs-server.service"],
        ["systemctl", "stop", "sbs-server.service"],
        ["systemctl", "show", "--property=LoadState", "--value", "sbs-webui.service"],
        ["systemctl", "disable", "sbs-webui.service"],
        ["systemctl", "stop", "sbs-webui.service"],
        ["systemctl", "start", "one-kvm.service"],
        ["systemctl", "enable", "one-kvm.service"],
    ]


@pytest.mark.asyncio
async def test_set_active_application_starts_streambox_studio_services(application_manager):
    calls = []

    def run_command(args, timeout=30):
        calls.append(args)
        if args[:4] == ["systemctl", "show", "--property=LoadState", "--value"]:
            return True, "loaded"
        return True, ""

    application_manager._run_command = run_command

    success = await application_manager.set_active_application("streambox-studio")

    assert success is True
    assert calls == [
        ["systemctl", "show", "--property=LoadState", "--value", "sbs-server.service"],
        ["systemctl", "show", "--property=LoadState", "--value", "sbs-webui.service"],
        ["systemctl", "show", "--property=LoadState", "--value", "gst-manager.service"],
        ["systemctl", "disable", "gst-manager.service"],
        ["systemctl", "stop", "gst-manager.service"],
        ["systemctl", "show", "--property=LoadState", "--value", "one-kvm.service"],
        ["systemctl", "disable", "one-kvm.service"],
        ["systemctl", "stop", "one-kvm.service"],
        ["systemctl", "start", "sbs-server.service"],
        ["systemctl", "enable", "sbs-server.service"],
        ["systemctl", "start", "sbs-webui.service"],
        ["systemctl", "enable", "sbs-webui.service"],
    ]


@pytest.mark.asyncio
async def test_set_active_application_rejects_invalid_id(application_manager):
    with pytest.raises(ValueError):
        await application_manager.set_active_application("invalid")


@pytest.mark.asyncio
async def test_set_active_application_fails_when_target_missing(application_manager):
    application_manager._run_command = lambda args, timeout=30: (True, "not-found")

    success = await application_manager.set_active_application("one-kvm")

    assert success is False
