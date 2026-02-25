#!/usr/bin/env python3

import asyncio
import json
import logging
from typing import Any, Dict, List

try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import GLib
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    raise

from basic import BasicSettingsManager
from config import ConfigManager
from network import NetworkManager

logger = logging.getLogger(__name__)


class DBusError(Exception):
    def __init__(self, error_name: str, message: str):
        self.error_name = error_name
        self.message = message
        super().__init__(message)


class StreamboxSettingsInterface(dbus.service.Object):
    def __init__(self, config_manager: ConfigManager, bus):
        self.config_manager = config_manager
        self.basic_manager = BasicSettingsManager()
        self.network_manager = NetworkManager()
        self._loop = asyncio.get_event_loop()
        self._callbacks = {}
        
        super().__init__(bus, "/org/cockpit/StreamboxSettings")

    async def _async_init(self):
        await self.basic_manager.initialize()
        await self.network_manager.initialize()

    def cleanup(self):
        pass

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="", out_signature="a{sv}"
    )
    def GetBasicSettings(self) -> Dict[str, Any]:
        try:
            settings = self._loop.run_until_complete(
                self.basic_manager.get_basic_settings()
            )
            return settings
        except Exception as e:
            logger.error(f"GetBasicSettings error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def SetHostname(self, hostname: str) -> bool:
        try:
            success = self._loop.run_until_complete(
                self.basic_manager.set_hostname(hostname)
            )
            if success:
                self.BasicSettingsChanged()
            return success
        except Exception as e:
            logger.error(f"SetHostname error: {e}")
            raise DBusError("InvalidHostname", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def SetTimezone(self, timezone: str) -> bool:
        try:
            success = self._loop.run_until_complete(
                self.basic_manager.set_timezone(timezone)
            )
            if success:
                self.BasicSettingsChanged()
            return success
        except Exception as e:
            logger.error(f"SetTimezone error: {e}")
            raise DBusError("InvalidTimezone", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def SetLocale(self, locale: str) -> bool:
        try:
            success = self._loop.run_until_complete(
                self.basic_manager.set_locale(locale)
            )
            if success:
                self.BasicSettingsChanged()
            return success
        except Exception as e:
            logger.error(f"SetLocale error: {e}")
            raise DBusError("InvalidLocale", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="", out_signature="as"
    )
    def GetAvailableTimezones(self) -> List[str]:
        try:
            return self._loop.run_until_complete(
                self.basic_manager.get_available_timezones()
            )
        except Exception as e:
            logger.error(f"GetAvailableTimezones error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="", out_signature="as"
    )
    def GetAvailableLocales(self) -> List[str]:
        try:
            return self._loop.run_until_complete(
                self.basic_manager.get_available_locales()
            )
        except Exception as e:
            logger.error(f"GetAvailableLocales error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="", out_signature="s"
    )
    def GetConfig(self) -> str:
        try:
            return json.dumps(self.config_manager.config, indent=2)
        except Exception as e:
            logger.error(f"GetConfig error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def SetConfig(self, config_json: str) -> bool:
        try:
            config = json.loads(config_json)
            self.config_manager.config = config
            self._loop.run_until_complete(self.config_manager.save())
            self.ConfigChanged(config_json)
            return True
        except json.JSONDecodeError as e:
            logger.error(f"SetConfig error: {e}")
            raise DBusError("InvalidConfig", str(e))
        except Exception as e:
            logger.error(f"SetConfig error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="s"
    )
    def ExportConfig(self, profile_name: str) -> str:
        try:
            profile = self._loop.run_until_complete(
                self.config_manager.export_config(profile_name)
            )
            return json.dumps(profile, indent=2)
        except Exception as e:
            logger.error(f"ExportConfig error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="sb", out_signature="b"
    )
    def ImportConfig(self, config_json: str, apply: bool) -> bool:
        try:
            success = self._loop.run_until_complete(
                self.config_manager.import_config(config_json, apply)
            )
            if success and apply:
                self.ConfigChanged(config_json)
            return success
        except Exception as e:
            logger.error(f"ImportConfig error: {e}")
            raise DBusError("InvalidConfig", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="", out_signature="as"
    )
    def GetProfiles(self) -> List[str]:
        try:
            return self._loop.run_until_complete(
                self.config_manager.list_profiles()
            )
        except Exception as e:
            logger.error(f"GetProfiles error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def LoadProfile(self, profile_name: str) -> bool:
        try:
            success = self._loop.run_until_complete(
                self.config_manager.load_profile(profile_name)
            )
            if success:
                self.ConfigChanged(self.GetConfig())
            return success
        except Exception as e:
            logger.error(f"LoadProfile error: {e}")
            raise DBusError("ProfileNotFound", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def SaveProfile(self, profile_name: str) -> bool:
        try:
            success = self._loop.run_until_complete(
                self.config_manager.save_profile(profile_name)
            )
            return success
        except Exception as e:
            logger.error(f"SaveProfile error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def DeleteProfile(self, profile_name: str) -> bool:
        try:
            success = self._loop.run_until_complete(
                self.config_manager.delete_profile(profile_name)
            )
            return success
        except Exception as e:
            logger.error(f"DeleteProfile error: {e}")
            raise DBusError("ProfileNotFound", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="", out_signature="s"
    )
    def GetTvserverConfig(self) -> str:
        try:
            config = self._loop.run_until_complete(
                self.config_manager.get_tvserver_config()
            )
            return json.dumps(config, indent=2)
        except Exception as e:
            logger.error(f"GetTvserverConfig error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def SetTvserverConfig(self, config_json: str) -> bool:
        try:
            config = json.loads(config_json)
            success = self._loop.run_until_complete(
                self.config_manager.set_tvserver_config(config)
            )
            if success:
                self.TvserverConfigChanged(config_json)
            return success
        except json.JSONDecodeError as e:
            logger.error(f"SetTvserverConfig error: {e}")
            raise DBusError("InvalidConfig", str(e))
        except Exception as e:
            logger.error(f"SetTvserverConfig error: {e}")
            raise DBusError("TvserverConfigError", str(e))

    # ==================== Network Methods ====================

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="", out_signature="s"
    )
    def GetNetworkStatus(self) -> str:
        """Get comprehensive network status as JSON."""
        try:
            status = self._loop.run_until_complete(
                self.network_manager.get_network_status()
            )
            return json.dumps(status)
        except Exception as e:
            logger.error(f"GetNetworkStatus error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="s"
    )
    def GetWiredConfig(self, interface: str) -> str:
        """Get wired interface configuration as JSON."""
        try:
            config = self._loop.run_until_complete(
                self.network_manager.get_wired_config(interface or "eth0")
            )
            return json.dumps(config)
        except Exception as e:
            logger.error(f"GetWiredConfig error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def SetWiredConfig(self, config_json: str) -> bool:
        """Set wired interface configuration from JSON."""
        try:
            config = json.loads(config_json)
            success = self._loop.run_until_complete(
                self.network_manager.set_wired_config(config)
            )
            if success:
                self.NetworkConfigChanged()
            return success
        except json.JSONDecodeError as e:
            logger.error(f"SetWiredConfig error: {e}")
            raise DBusError("InvalidConfig", str(e))
        except Exception as e:
            logger.error(f"SetWiredConfig error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="s"
    )
    def ScanWifiNetworks(self, interface: str) -> str:
        """Scan for available WiFi networks, returns JSON array."""
        try:
            networks = self._loop.run_until_complete(
                self.network_manager.scan_wifi_networks(interface or "wlan0")
            )
            return json.dumps(networks)
        except Exception as e:
            logger.error(f"ScanWifiNetworks error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def ConnectWifi(self, config_json: str) -> bool:
        """Connect to a WiFi network. Config includes interface, ssid, password, method, ip_config."""
        try:
            config = json.loads(config_json)
            interface = config.get("interface", "wlan0")
            ssid = config.get("ssid", "")
            password = config.get("password", "")
            method = config.get("method", "dhcp")
            ip_config = config.get("ip_config")
            
            success = self._loop.run_until_complete(
                self.network_manager.connect_wifi(ssid, password, interface, method, ip_config)
            )
            if success:
                self.NetworkConfigChanged()
            return success
        except json.JSONDecodeError as e:
            logger.error(f"ConnectWifi error: {e}")
            raise DBusError("InvalidConfig", str(e))
        except Exception as e:
            logger.error(f"ConnectWifi error: {e}")
            raise DBusError("ConnectionFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="", out_signature="s"
    )
    def GetWifiApConfig(self) -> str:
        """Get WiFi AP configuration as JSON."""
        try:
            config = self._loop.run_until_complete(
                self.network_manager.get_wifi_ap_config()
            )
            return json.dumps(config)
        except Exception as e:
            logger.error(f"GetWifiApConfig error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def SetWifiApConfig(self, config_json: str) -> bool:
        """Set WiFi AP configuration from JSON."""
        try:
            config = json.loads(config_json)
            success = self._loop.run_until_complete(
                self.network_manager.set_wifi_ap_config(config)
            )
            if success:
                self.NetworkConfigChanged()
            return success
        except json.JSONDecodeError as e:
            logger.error(f"SetWifiApConfig error: {e}")
            raise DBusError("InvalidConfig", str(e))
        except Exception as e:
            logger.error(f"SetWifiApConfig error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="s"
    )
    def GetWifiClientConfig(self, interface: str) -> str:
        """Get WiFi client configuration as JSON."""
        try:
            config = self._loop.run_until_complete(
                self.network_manager.get_wifi_client_config(interface or "wlan0")
            )
            return json.dumps(config)
        except Exception as e:
            logger.error(f"GetWifiClientConfig error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def DisconnectWifi(self, interface: str) -> bool:
        """Disconnect from WiFi network."""
        try:
            success = self._loop.run_until_complete(
                self.network_manager.disconnect_wifi(interface or "wlan0")
            )
            if success:
                self.NetworkConfigChanged()
            return success
        except Exception as e:
            logger.error(f"DisconnectWifi error: {e}")
            raise DBusError("OperationFailed", str(e))

    # ==================== HDMI Loopout Settings ====================

    HDMI_CONFIG_PATH = "/etc/streambox-tv/config.json"

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="", out_signature="s"
    )
    def GetHdmiConfig(self) -> str:
        """Get HDMI Loopout configuration from streambox-tv config.json."""
        try:
            # Default config matching streambox-tv defaults
            config = {
                "video": {
                    "game_mode": 2,
                    "vrr_mode": 2,
                    "hdmi_source": "HDMI2"
                },
                "audio": {
                    "enabled": True,
                    "capture_device": "hw:0,2",
                    "playback_device": "hw:0,0",
                    "latency_us": 10000,
                    "sample_format": "S16_LE",
                    "channels": 2,
                    "sample_rate": 48000
                },
                "hdcp": {
                    "enabled": False,
                    "version": "auto"
                },
                "debug": {
                    "trace_level": 0
                }
            }
            
            # Read existing config if present
            try:
                with open(self.HDMI_CONFIG_PATH, "r") as f:
                    existing = json.load(f)
                    # Merge existing config
                    for key in config:
                        if key in existing and isinstance(existing[key], dict):
                            config[key].update(existing[key])
            except (IOError, json.JSONDecodeError):
                logger.info("No HDMI config file found, using defaults")
            
            return json.dumps(config)
        except Exception as e:
            logger.error(f"GetHdmiConfig error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def SetHdmiConfig(self, config_json: str) -> bool:
        """Set HDMI Loopout configuration to streambox-tv config.json."""
        try:
            import subprocess
            import os
            
            config = json.loads(config_json)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.HDMI_CONFIG_PATH), exist_ok=True)
            
            # Write JSON config
            with open(self.HDMI_CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Wrote HDMI config to {self.HDMI_CONFIG_PATH}")
            
            # Send SIGHUP to streambox-tv to reload config (it watches the file)
            # This avoids a full restart and is faster
            result = subprocess.run(
                ["pkill", "-HUP", "streambox-tv"],
                capture_output=True,
                timeout=5
            )
            
            # If pkill fails (process not running), that's fine
            success = True
            self.TvserverConfigChanged(config_json)
            
            return success
            
        except json.JSONDecodeError as e:
            logger.error(f"SetHdmiConfig error: {e}")
            raise DBusError("InvalidConfig", str(e))
        except Exception as e:
            logger.error(f"SetHdmiConfig error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="", out_signature="s"
    )
    def GetAudioDevices(self) -> str:
        """Get available audio devices using aplay -l and arecord -l."""
        try:
            import subprocess
            
            devices = {
                "playback": [],
                "capture": []
            }
            
            # Get playback devices
            result = subprocess.run(["aplay", "-l"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith("card "):
                        # Parse: "card 0: AMLAUGESOUND [AML-AUGESOUND], device 0: ..."
                        parts = line.split(":")
                        if len(parts) >= 2:
                            card_part = parts[0].replace("card ", "")
                            device_match = line.split("device ")
                            if len(device_match) >= 2:
                                device_num = device_match[1].split(":")[0]
                                name_part = parts[1].split("[")[0].strip() if "[" in parts[1] else parts[1].split(",")[0].strip()
                                hw_addr = f"hw:{card_part},{device_num}"
                                devices["playback"].append({
                                    "address": hw_addr,
                                    "name": name_part,
                                    "description": line.strip()
                                })
            
            # Get capture devices
            result = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith("card "):
                        parts = line.split(":")
                        if len(parts) >= 2:
                            card_part = parts[0].replace("card ", "")
                            device_match = line.split("device ")
                            if len(device_match) >= 2:
                                device_num = device_match[1].split(":")[0]
                                name_part = parts[1].split("[")[0].strip() if "[" in parts[1] else parts[1].split(",")[0].strip()
                                hw_addr = f"hw:{card_part},{device_num}"
                                devices["capture"].append({
                                    "address": hw_addr,
                                    "name": name_part,
                                    "description": line.strip()
                                })
            
            return json.dumps(devices)
        except Exception as e:
            logger.error(f"GetAudioDevices error: {e}")
            raise DBusError("OperationFailed", str(e))

    # ==================== Storage Settings ====================

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="", out_signature="s"
    )
    def GetStorageInfo(self) -> str:
        """Get storage device information using df and lsblk."""
        try:
            import subprocess
            
            filesystems = []
            
            # Get filesystem info from df
            result = subprocess.run(
                ["df", "-B1", "--output=source,target,fstype,size,used,avail,pcent"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 7 and not parts[0].startswith("tmpfs") and not parts[0].startswith("devtmpfs"):
                        # Get label using lsblk
                        label = ""
                        try:
                            lsblk_result = subprocess.run(
                                ["lsblk", "-no", "LABEL", parts[0]],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if lsblk_result.returncode == 0:
                                label = lsblk_result.stdout.strip()
                        except:
                            pass
                        
                        use_percent = parts[6].replace("%", "")
                        try:
                            use_percent = int(use_percent)
                        except:
                            use_percent = 0
                        
                        filesystems.append({
                            "device": parts[0],
                            "mount_point": parts[1],
                            "fstype": parts[2],
                            "size": int(parts[3]),
                            "used": int(parts[4]),
                            "available": int(parts[5]),
                            "use_percent": use_percent,
                            "label": label
                        })
            
            return json.dumps({"filesystems": filesystems})
        except Exception as e:
            logger.error(f"GetStorageInfo error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def MountDevice(self, device: str) -> bool:
        """Mount a storage device."""
        try:
            import subprocess
            import os
            
            # Sanitize device path
            if not device.startswith("/dev/"):
                device = "/dev/" + device
            
            # Get filesystem label for mount point
            label = ""
            try:
                result = subprocess.run(
                    ["lsblk", "-no", "LABEL", device],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    label = result.stdout.strip()
            except:
                pass
            
            # Create mount point
            mount_point = f"/media/{label}" if label else f"/media/{os.path.basename(device)}"
            os.makedirs(mount_point, exist_ok=True)
            
            # Mount device
            result = subprocess.run(
                ["mount", device, mount_point],
                capture_output=True,
                timeout=30
            )
            
            success = result.returncode == 0
            if success:
                logger.info(f"Mounted {device} at {mount_point}")
            else:
                logger.error(f"Mount failed: {result.stderr.decode()}")
            
            return success
        except Exception as e:
            logger.error(f"MountDevice error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.method(
        "org.cockpit.StreamboxSettings",
        in_signature="s", out_signature="b"
    )
    def UnmountDevice(self, device: str) -> bool:
        """Unmount a storage device."""
        try:
            import subprocess
            
            # Sanitize device path
            if not device.startswith("/dev/"):
                device = "/dev/" + device
            
            # Unmount device
            result = subprocess.run(
                ["umount", device],
                capture_output=True,
                timeout=30
            )
            
            success = result.returncode == 0
            if success:
                logger.info(f"Unmounted {device}")
            else:
                logger.error(f"Unmount failed: {result.stderr.decode()}")
            
            return success
        except Exception as e:
            logger.error(f"UnmountDevice error: {e}")
            raise DBusError("OperationFailed", str(e))

    @dbus.service.signal("org.cockpit.StreamboxSettings")
    def BasicSettingsChanged(self):
        pass

    @dbus.service.signal("org.cockpit.StreamboxSettings", signature="s")
    def ConfigChanged(self, config_json: str):
        pass

    @dbus.service.signal("org.cockpit.StreamboxSettings", signature="s")
    def TvserverConfigChanged(self, config_json: str):
        pass

    @dbus.service.signal("org.cockpit.StreamboxSettings")
    def NetworkConfigChanged(self):
        """Signal emitted when network configuration changes."""
        pass

