#!/usr/bin/env python3

import asyncio
import logging
import subprocess
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class BasicSettingsManager:
    def __init__(self):
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        logger.info("Initializing BasicSettingsManager")
        self._initialized = True

    def _run_command(self, args: List[str]) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {' '.join(args)}")
            return False, ""
        except FileNotFoundError:
            logger.error(f"Command not found: {args[0]}")
            return False, ""
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return False, ""

    async def get_hostname(self) -> str:
        success, hostname = self._run_command(["hostnamectl", "--static", "transient"])
        if success:
            return hostname
        return "streambox"

    async def set_hostname(self, hostname: str) -> bool:
        if not self._validate_hostname(hostname):
            logger.error(f"Invalid hostname: {hostname}")
            return False

        success, _ = self._run_command(["hostnamectl", "set-hostname", hostname])
        if success:
            logger.info(f"Hostname set to: {hostname}")
            return True

        logger.error(f"Failed to set hostname: {hostname}")
        return False

    def _validate_hostname(self, hostname: str) -> bool:
        if not hostname or len(hostname) > 253:
            return False

        if hostname[-1] == ".":
            hostname = hostname[:-1]

        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.")
        return all(c in allowed for c in hostname) and not hostname.startswith("-")

    async def get_timezone(self) -> str:
        success, timezone = self._run_command(["timedatectl", "show", "-p", "Timezone", "--value"])
        if success:
            return timezone
        return "UTC"

    async def set_timezone(self, timezone: str) -> bool:
        available_timezones = await self.get_available_timezones()
        if timezone not in available_timezones:
            logger.error(f"Invalid timezone: {timezone}")
            return False

        success, _ = self._run_command(["timedatectl", "set-timezone", timezone])
        if success:
            logger.info(f"Timezone set to: {timezone}")
            return True

        logger.error(f"Failed to set timezone: {timezone}")
        return False

    async def get_available_timezones(self) -> List[str]:
        success, output = self._run_command(["timedatectl", "list-timezones"])
        if success:
            return output.split("\n")
        return ["UTC"]

    async def get_locale(self) -> str:
        success, output = self._run_command(["localectl", "status", "--no-pager"])
        if success:
            for line in output.split("\n"):
                if line.strip().startswith("LANG="):
                    return line.split("=")[1].strip()
        return "en_US.UTF-8"

    async def set_locale(self, locale: str) -> bool:
        available_locales = await self.get_available_locales()
        if locale not in available_locales:
            logger.error(f"Invalid locale: {locale}")
            return False

        success, _ = self._run_command(["localectl", "set-locale", f"LANG={locale}"])
        if success:
            logger.info(f"Locale set to: {locale}")
            return True

        logger.error(f"Failed to set locale: {locale}")
        return False

    async def get_available_locales(self) -> List[str]:
        success, output = self._run_command(["locale", "-a"])
        if success and output:
            locales = []
            for line in output.split("\n"):
                if line and line.strip():
                    locales.append(line.strip())
            
            if locales:
                return sorted(list(set(locales)))
        
        logger.warning("Failed to get locales from system, using fallback list")
        return ["en_US.utf8", "en_US.UTF-8", "C.utf8", "C.UTF-8", "en_GB.utf8", "zh_CN.utf8", "zh_TW.utf8", "ja_JP.utf8", "ko_KR.utf8", "de_DE.utf8", "fr_FR.utf8", "es_ES.utf8"]

    async def get_ntp_server(self) -> str:
        success, output = self._run_command(["timedatectl", "show", "-p", "NTP", "--value"])
        if success:
            return "yes" if output == "yes" else "no"
        return "yes"

    async def set_ntp_server(self, ntp_server: str) -> bool:
        if ntp_server == "yes" or ntp_server:
            success, _ = self._run_command(["timedatectl", "set-ntp", "true"])
        else:
            success, _ = self._run_command(["timedatectl", "set-ntp", "false"])

        if success:
            logger.info(f"NTP set to: {ntp_server}")
            return True

        logger.error(f"Failed to set NTP: {ntp_server}")
        return False

    async def get_basic_settings(self) -> Dict[str, str]:
        settings = {}
        
        hostname = await self.get_hostname()
        settings["hostname"] = hostname
        
        timezone = await self.get_timezone()
        settings["timezone"] = timezone
        
        locale = await self.get_locale()
        settings["locale"] = locale
        
        ntp_server = await self.get_ntp_server()
        settings["ntp_server"] = ntp_server
        
        return settings

    async def set_basic_settings(self, settings: Dict[str, str]) -> bool:
        success = True
        
        if "hostname" in settings:
            if not await self.set_hostname(settings["hostname"]):
                success = False
        
        if "timezone" in settings:
            if not await self.set_timezone(settings["timezone"]):
                success = False
        
        if "locale" in settings:
            if not await self.set_locale(settings["locale"]):
                success = False
        
        if "ntp_server" in settings:
            if not await self.set_ntp_server(settings["ntp_server"]):
                success = False
        
        return success
