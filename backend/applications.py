#!/usr/bin/env python3

import logging
import subprocess
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ApplicationManager:
    """Manages the mutually exclusive Streambox application services."""

    DEFAULT_APPLICATION = "gst-manager"
    APPLICATIONS = {
        "gst-manager": {
            "name": "GStreamer Manager",
            "service": "gst-manager.service",
        },
        "one-kvm": {
            "name": "One-KVM",
            "service": "one-kvm.service",
        },
    }

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the application manager."""
        if self._initialized:
            return
        logger.info("Initializing ApplicationManager")
        self._initialized = True

    def _run_command(self, args: List[str], timeout: int = 30) -> Tuple[bool, str]:
        """Run a command and return success status plus combined output."""
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = "\n".join(
                part.strip() for part in (result.stdout, result.stderr) if part.strip()
            )
            return result.returncode == 0, output
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {' '.join(args)}")
            return False, ""
        except FileNotFoundError:
            logger.error(f"Command not found: {args[0]}")
            return False, ""
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return False, ""

    def _service_available(self, service: str) -> bool:
        success, output = self._run_command(
            ["systemctl", "show", "--property=LoadState", "--value", service]
        )
        return success and output.strip() == "loaded"

    def _service_active(self, service: str) -> bool:
        success, _ = self._run_command(["systemctl", "is-active", "--quiet", service])
        return success

    def _service_enabled(self, service: str) -> bool:
        success, _ = self._run_command(["systemctl", "is-enabled", "--quiet", service])
        return success

    def _systemctl(self, action: str, service: str) -> bool:
        success, output = self._run_command(["systemctl", action, service])
        if not success:
            logger.error(f"systemctl {action} {service} failed: {output}")
        return success

    async def get_status(self) -> Dict[str, Any]:
        """Get application availability and active service status."""
        applications = []
        active_ids = []
        enabled_ids = []

        for app_id, app in self.APPLICATIONS.items():
            service = app["service"]
            available = self._service_available(service)
            active = available and self._service_active(service)
            enabled = available and self._service_enabled(service)

            if active:
                active_ids.append(app_id)
            if enabled:
                enabled_ids.append(app_id)

            applications.append({
                "id": app_id,
                "name": app["name"],
                "service": service,
                "available": available,
                "active": active,
                "enabled": enabled,
            })

        selected_application = self.DEFAULT_APPLICATION
        if len(active_ids) == 1:
            selected_application = active_ids[0]
        elif not active_ids and len(enabled_ids) == 1:
            selected_application = enabled_ids[0]
        elif self.DEFAULT_APPLICATION in active_ids or self.DEFAULT_APPLICATION in enabled_ids:
            selected_application = self.DEFAULT_APPLICATION

        return {
            "active_application": selected_application,
            "default_application": self.DEFAULT_APPLICATION,
            "applications": applications,
            "conflict": len(active_ids) > 1,
        }

    async def set_active_application(self, application_id: str) -> bool:
        """Switch to one application by disabling/stopping the other service."""
        if application_id not in self.APPLICATIONS:
            raise ValueError(f"Invalid application: {application_id}")

        target_service = self.APPLICATIONS[application_id]["service"]
        if not self._service_available(target_service):
            logger.error(f"Target service is not available: {target_service}")
            return False

        for other_id, other_app in self.APPLICATIONS.items():
            if other_id == application_id:
                continue

            other_service = other_app["service"]
            if not self._service_available(other_service):
                logger.warning(f"Skipping unavailable service: {other_service}")
                continue

            if not self._systemctl("disable", other_service):
                return False
            if not self._systemctl("stop", other_service):
                return False

        if not self._systemctl("start", target_service):
            return False
        if not self._systemctl("enable", target_service):
            return False

        logger.info(f"Active application switched to: {application_id}")
        return True
