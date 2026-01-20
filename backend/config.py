#!/usr/bin/env python3

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    CONFIG_DIR = Path("/var/lib/streambox-settings")
    CONFIG_FILE = CONFIG_DIR / "config.json"
    PROFILES_DIR = CONFIG_DIR / "profiles"
    TVSERVER_CONFIG_FILE = Path("/etc/streambox-tv/config.json")

    DEFAULT_CONFIG = {
        "basic": {
            "hostname": "streambox",
            "timezone": "UTC",
            "locale": "en_US.UTF-8",
            "ntp_server": "pool.ntp.org"
        },
        "network": {
            "wired": {
                "interface": "eth0",
                "method": "dhcp",
                "ip_address": None,
                "netmask": None,
                "gateway": None,
                "dns_servers": []
            },
            "wifi_client": {
                "interface": "wlan0",
                "ssid": None,
                "security": None,
                "password": None,
                "method": "dhcp",
                "ip_address": None,
                "netmask": None,
                "gateway": None,
                "dns_servers": []
            },
            "wifi_ap": {
                "enabled": False,
                "interface": "wlan0",
                "ssid": "StreamBox-AP",
                "security": "WPA2",
                "password": None,
                "dhcp_enabled": True,
                "ip_address": "192.168.4.1",
                "ip_range_start": "192.168.4.100",
                "ip_range_end": "192.168.4.200"
            }
        }
    }

    def __init__(self):
        self.config: Dict[str, Any] = {}
        self._watchers: List[asyncio.Task] = []
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        logger.info("Initializing ConfigManager")

        self._ensure_directories()
        await self._load_config()
        
        if not self.TVSERVER_CONFIG_FILE.exists():
            logger.warning("TVServer config file not found")
        
        self._initialized = True
        logger.info("ConfigManager initialized successfully")

    def _ensure_directories(self):
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    async def _load_config(self):
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    loaded_config = json.load(f)
                    self._merge_config(loaded_config)
                logger.info(f"Loaded configuration from {self.CONFIG_FILE}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load config: {e}, using defaults")
                self.config = self._deep_copy(self.DEFAULT_CONFIG)
        else:
            logger.info("No existing config found, using defaults")
            self.config = self._deep_copy(self.DEFAULT_CONFIG)
            await self._save_config()

    def _merge_config(self, loaded_config: Dict[str, Any]):
        self.config = self._deep_copy(self.DEFAULT_CONFIG)
        self._deep_update(self.config, loaded_config)

    def _deep_copy(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        return obj

    def _deep_update(self, base: Dict, update: Dict):
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    async def _save_config(self):
        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.CONFIG_FILE}")
        except IOError as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        return self.config.get(section, {})

    def set_section(self, section: str, data: Dict[str, Any]) -> None:
        self.config[section] = data

    async def save(self) -> None:
        await self._save_config()

    async def reload(self) -> None:
        await self._load_config()

    async def export_config(self, profile_name: str) -> Dict[str, Any]:
        profile_data = {
            "name": profile_name,
            "config": self._deep_copy(self.config)
        }
        return profile_data

    async def import_config(self, config_json: str, apply: bool = False) -> bool:
        try:
            imported_config = json.loads(config_json)
            if "config" in imported_config:
                imported_config = imported_config["config"]
            
            if apply:
                self._merge_config(imported_config)
                await self._save_config()
            
            return True
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to import config: {e}")
            return False

    async def list_profiles(self) -> List[str]:
        profiles = []
        for profile_file in self.PROFILES_DIR.glob("*.json"):
            profiles.append(profile_file.stem)
        return sorted(profiles)

    async def load_profile(self, profile_name: str) -> bool:
        profile_file = self.PROFILES_DIR / f"{profile_name}.json"
        if not profile_file.exists():
            logger.error(f"Profile not found: {profile_name}")
            return False

        try:
            with open(profile_file, "r") as f:
                profile_data = json.load(f)
                if "config" in profile_data:
                    self._merge_config(profile_data["config"])
                    await self._save_config()
                    logger.info(f"Loaded profile: {profile_name}")
                    return True
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load profile: {e}")
            return False

        return False

    async def save_profile(self, profile_name: str) -> bool:
        profile_file = self.PROFILES_DIR / f"{profile_name}.json"
        profile_data = {
            "name": profile_name,
            "config": self._deep_copy(self.config)
        }

        try:
            with open(profile_file, "w") as f:
                json.dump(profile_data, f, indent=2)
            logger.info(f"Saved profile: {profile_name}")
            return True
        except IOError as e:
            logger.error(f"Failed to save profile: {e}")
            return False

    async def delete_profile(self, profile_name: str) -> bool:
        profile_file = self.PROFILES_DIR / f"{profile_name}.json"
        if not profile_file.exists():
            logger.error(f"Profile not found: {profile_name}")
            return False

        try:
            profile_file.unlink()
            logger.info(f"Deleted profile: {profile_name}")
            return True
        except IOError as e:
            logger.error(f"Failed to delete profile: {e}")
            return False

    async def get_tvserver_config(self) -> Dict[str, Any]:
        if not self.TVSERVER_CONFIG_FILE.exists():
            return {}

        try:
            with open(self.TVSERVER_CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load tvserver config: {e}")
            return {}

    async def set_tvserver_config(self, config: Dict[str, Any]) -> bool:
        try:
            with open(self.TVSERVER_CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved tvserver configuration to {self.TVSERVER_CONFIG_FILE}")
            return True
        except IOError as e:
            logger.error(f"Failed to save tvserver config: {e}")
            return False

    async def cleanup(self):
        logger.info("Cleaning up ConfigManager")
        for task in self._watchers:
            task.cancel()
        self._watchers.clear()
