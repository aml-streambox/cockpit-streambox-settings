#!/usr/bin/env python3

import asyncio
import json
import logging
import subprocess
import re
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class NetworkManager:
    """Manages network configuration for wired and wireless interfaces."""
    
    # Only show these interfaces
    ALLOWED_INTERFACES = ["eth0", "wlan0", "wlan1"]

    def __init__(self):
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        logger.info("Initializing NetworkManager")
        self._initialized = True

    def _run_command(self, args: List[str], timeout: int = 30) -> tuple[bool, str]:
        """Run a shell command and return success status and output."""
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout
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

    async def get_interfaces(self) -> List[Dict[str, Any]]:
        """Get list of network interfaces with their status."""
        interfaces = []
        
        # Get interface list using ip command
        success, output = self._run_command(["ip", "-j", "link", "show"])
        if success and output:
            try:
                links = json.loads(output)
                for link in links:
                    name = link.get("ifname", "")
                    # Only include allowed interfaces
                    if name not in self.ALLOWED_INTERFACES:
                        continue
                    
                    iface = {
                        "name": name,
                        "type": self._get_interface_type(name),
                        "state": link.get("operstate", "unknown").lower(),
                        "mac": link.get("address", ""),
                        "ip_address": None,
                        "netmask": None,
                        "gateway": None
                    }
                    
                    # Get IP address
                    ip_info = await self._get_interface_ip(name)
                    iface.update(ip_info)
                    
                    interfaces.append(iface)
            except json.JSONDecodeError:
                logger.error("Failed to parse ip link output")
        else:
            # Fallback without JSON
            success, output = self._run_command(["ip", "link", "show"])
            if success:
                for line in output.split("\n"):
                    match = re.match(r"^\d+:\s+(\w+):", line)
                    if match:
                        name = match.group(1)
                        if name in self.ALLOWED_INTERFACES:
                            interfaces.append({
                                "name": name,
                                "type": self._get_interface_type(name),
                                "state": "unknown",
                                "mac": "",
                                "ip_address": None,
                                "netmask": None,
                                "gateway": None
                            })
        
        return interfaces

    def _get_interface_type(self, name: str) -> str:
        """Determine interface type based on name."""
        if name.startswith("eth") or name.startswith("enp"):
            return "wired"
        elif name.startswith("wlan") or name.startswith("wlp"):
            return "wifi"
        elif name.startswith("br"):
            return "bridge"
        return "other"

    async def _get_interface_ip(self, interface: str) -> Dict[str, Any]:
        """Get IP configuration for an interface."""
        result = {"ip_address": None, "netmask": None, "gateway": None}
        
        success, output = self._run_command(["ip", "-j", "addr", "show", interface])
        if success and output:
            try:
                data = json.loads(output)
                if data and data[0].get("addr_info"):
                    for addr in data[0]["addr_info"]:
                        if addr.get("family") == "inet":
                            result["ip_address"] = addr.get("local")
                            prefix = addr.get("prefixlen", 24)
                            result["netmask"] = self._prefix_to_netmask(prefix)
                            break
            except (json.JSONDecodeError, IndexError, KeyError):
                pass
        
        # Get gateway
        success, output = self._run_command(["ip", "route", "show", "default"])
        if success and output:
            match = re.search(r"default via (\S+)", output)
            if match:
                result["gateway"] = match.group(1)
        
        return result

    def _prefix_to_netmask(self, prefix: int) -> str:
        """Convert CIDR prefix to netmask."""
        mask = (0xffffffff >> (32 - prefix)) << (32 - prefix)
        return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"

    async def get_network_status(self) -> Dict[str, Any]:
        """Get comprehensive network status."""
        interfaces = await self.get_interfaces()
        
        # Get DNS servers
        dns_servers = await self._get_dns_servers()
        
        return {
            "interfaces": interfaces,
            "dns_servers": dns_servers
        }

    async def _get_dns_servers(self) -> List[str]:
        """Get configured DNS servers."""
        dns_servers = []
        try:
            with open("/etc/resolv.conf", "r") as f:
                for line in f:
                    if line.startswith("nameserver"):
                        parts = line.split()
                        if len(parts) >= 2:
                            dns_servers.append(parts[1])
        except IOError:
            pass
        return dns_servers

    async def get_wired_config(self, interface: str = "eth0") -> Dict[str, Any]:
        """Get wired interface configuration."""
        config = {
            "interface": interface,
            "method": "dhcp",
            "ip_address": None,
            "netmask": None,
            "gateway": None,
            "dns_servers": []
        }
        
        # Get current IP info
        ip_info = await self._get_interface_ip(interface)
        config.update(ip_info)
        
        # Check if using DHCP by looking at dhcpcd leases
        success, output = self._run_command(["cat", f"/var/lib/dhcpcd/{interface}.lease"])
        if success and output:
            config["method"] = "dhcp"
        elif config["ip_address"]:
            config["method"] = "static"
        
        config["dns_servers"] = await self._get_dns_servers()
        
        return config

    async def set_wired_config(self, config: Dict[str, Any]) -> bool:
        """Set wired interface configuration."""
        interface = config.get("interface", "eth0")
        method = config.get("method", "dhcp")
        
        try:
            if method == "dhcp":
                # Enable DHCP
                self._run_command(["ip", "addr", "flush", "dev", interface])
                success, _ = self._run_command(["dhcpcd", interface])
                return success
            else:
                # Static IP configuration
                ip_address = config.get("ip_address")
                netmask = config.get("netmask", "255.255.255.0")
                gateway = config.get("gateway")
                
                if not ip_address:
                    logger.error("Static IP requires ip_address")
                    return False
                
                # Convert netmask to prefix
                prefix = self._netmask_to_prefix(netmask)
                
                # Flush and set IP
                self._run_command(["ip", "addr", "flush", "dev", interface])
                success, _ = self._run_command([
                    "ip", "addr", "add", f"{ip_address}/{prefix}", "dev", interface
                ])
                
                if not success:
                    return False
                
                # Set gateway
                if gateway:
                    self._run_command(["ip", "route", "del", "default"])
                    success, _ = self._run_command([
                        "ip", "route", "add", "default", "via", gateway
                    ])
                
                # Set DNS
                dns_servers = config.get("dns_servers", [])
                if dns_servers:
                    await self._set_dns_servers(dns_servers)
                
                logger.info(f"Set static IP {ip_address}/{prefix} on {interface}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to set wired config: {e}")
            return False

    def _netmask_to_prefix(self, netmask: str) -> int:
        """Convert netmask to CIDR prefix."""
        try:
            parts = [int(p) for p in netmask.split(".")]
            binary = "".join(format(p, "08b") for p in parts)
            return binary.count("1")
        except:
            return 24

    async def _set_dns_servers(self, dns_servers: List[str]) -> bool:
        """Set DNS servers in resolv.conf."""
        try:
            with open("/etc/resolv.conf", "w") as f:
                for dns in dns_servers:
                    f.write(f"nameserver {dns}\n")
            return True
        except IOError as e:
            logger.error(f"Failed to set DNS: {e}")
            return False

    async def scan_wifi_networks(self, interface: str = "wlan0") -> List[Dict[str, Any]]:
        """Scan for available WiFi networks."""
        networks = []
        
        # Bring interface up
        self._run_command(["ip", "link", "set", interface, "up"])
        
        # Use iw to scan
        success, output = self._run_command(["iw", "dev", interface, "scan"], timeout=15)
        if success:
            current_network = None
            
            for line in output.split("\n"):
                line = line.strip()
                
                if line.startswith("BSS "):
                    if current_network:
                        networks.append(current_network)
                    bssid = line.split()[1].replace("(", "").replace(")", "")
                    current_network = {
                        "bssid": bssid,
                        "ssid": "",
                        "signal": 0,
                        "security": "open",
                        "frequency": 0
                    }
                elif current_network:
                    if line.startswith("SSID:"):
                        current_network["ssid"] = line[5:].strip()
                    elif line.startswith("signal:"):
                        match = re.search(r"(-?\d+)", line)
                        if match:
                            current_network["signal"] = int(match.group(1))
                    elif line.startswith("freq:"):
                        match = re.search(r"(\d+)", line)
                        if match:
                            current_network["frequency"] = int(match.group(1))
                    elif "WPA" in line or "RSN" in line:
                        current_network["security"] = "wpa"
                    elif "WEP" in line:
                        current_network["security"] = "wep"
            
            if current_network:
                networks.append(current_network)
        
        # Filter out hidden networks (empty SSID)
        networks = [n for n in networks if n.get("ssid", "").strip()]
        
        # Sort by signal strength
        networks.sort(key=lambda x: x.get("signal", -100), reverse=True)
        
        return networks

    async def connect_wifi(self, ssid: str, password: str, interface: str = "wlan0", 
                           method: str = "dhcp", ip_config: Dict[str, Any] = None) -> bool:
        """Connect to a WiFi network using wpa_supplicant."""
        try:
            # Create wpa_supplicant config
            wpa_config = f'''
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
'''
            config_path = "/tmp/wpa_supplicant.conf"
            with open(config_path, "w") as f:
                f.write(wpa_config)
            
            # Stop any existing wpa_supplicant
            self._run_command(["killall", "wpa_supplicant"])
            
            # Start wpa_supplicant
            success, _ = self._run_command([
                "wpa_supplicant", "-B", "-i", interface,
                "-c", config_path, "-D", "nl80211,wext"
            ])
            
            if not success:
                return False
            
            await asyncio.sleep(2)
            
            if method == "dhcp":
                # Get IP via DHCP
                success, _ = self._run_command(["dhcpcd", interface])
            else:
                # Static IP configuration
                if ip_config:
                    ip_address = ip_config.get("ip_address")
                    netmask = ip_config.get("netmask", "255.255.255.0")
                    gateway = ip_config.get("gateway")
                    
                    if ip_address:
                        prefix = self._netmask_to_prefix(netmask)
                        self._run_command(["ip", "addr", "flush", "dev", interface])
                        self._run_command(["ip", "addr", "add", f"{ip_address}/{prefix}", "dev", interface])
                        if gateway:
                            self._run_command(["ip", "route", "add", "default", "via", gateway])
                        success = True
                    else:
                        success = False
                else:
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to connect WiFi: {e}")
            return False

    async def get_wifi_ap_config(self) -> Dict[str, Any]:
        """Get WiFi AP configuration."""
        config = {
            "enabled": False,
            "interface": "wlan1",
            "ssid": "StreamBox-AP",
            "security": "WPA2",
            "password": "",
            "channel": 36,
            "ip_address": "192.168.2.1"
        }
        
        # Check if hostapd is running (AP is enabled)
        success, output = self._run_command(["pgrep", "hostapd"])
        config["enabled"] = success
        
        # First, try to read from /etc/wifi/ap_config (managed by this plugin)
        try:
            with open("/etc/wifi/ap_config", "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    value = value.strip().strip('"')
                    if key == "SSID":
                        config["ssid"] = value
                    elif key == "PASSWORD":
                        config["password"] = value
                    elif key == "CHANNEL":
                        config["channel"] = int(value)
                    elif key == "IP_ADDRESS":
                        config["ip_address"] = value
        except IOError:
            # Fallback: read from hostapd_temp.conf
            hostapd_configs = ["/etc/hostapd_temp.conf", "/etc/hostapd/hostapd_temp.conf", 
                              "/etc/hostapd.conf", "/etc/hostapd/hostapd.conf"]
            for config_path in hostapd_configs:
                try:
                    with open(config_path, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("ssid="):
                                config["ssid"] = line.split("=", 1)[1].strip()
                            elif line.startswith("channel="):
                                config["channel"] = int(line.split("=", 1)[1].strip())
                            elif line.startswith("wpa_passphrase="):
                                config["password"] = line.split("=", 1)[1].strip()
                            elif line.startswith("interface="):
                                config["interface"] = line.split("=", 1)[1].strip()
                    break  # Found and read config, stop looking
                except IOError:
                    continue
        
        # Get current IP from interface when AP is enabled
        if config["enabled"]:
            interface = config.get("interface", "wlan1")
            ip_info = await self._get_interface_ip(interface)
            if ip_info.get("ip_address"):
                config["ip_address"] = ip_info["ip_address"]
        
        return config

    async def set_wifi_ap_config(self, config: Dict[str, Any]) -> bool:
        """Set WiFi AP configuration by writing to /etc/wifi/ap_config and restarting wifi-ap.service."""
        try:
            enabled = config.get("enabled", False)
            ssid = config.get("ssid", "StreamBox-AP")
            password = config.get("password", "")
            channel = config.get("channel", 36)
            ip_address = config.get("ip_address", "192.168.2.1")
            
            if not enabled:
                # Stop AP mode via systemctl
                self._run_command(["systemctl", "stop", "wifi-ap"])
                return True
            
            if len(password) < 8:
                logger.error("AP password must be at least 8 characters")
                return False
            
            # Write config to /etc/wifi/ap_config (sourced by wifi_ap_init)
            ap_config_content = f"""# WiFi AP Configuration
# Managed by cockpit-streambox-settings
SSID="{ssid}"
PASSWORD="{password}"
CHANNEL={channel}
IP_ADDRESS={ip_address}
"""
            # Ensure directory exists
            self._run_command(["mkdir", "-p", "/etc/wifi"])
            
            with open("/etc/wifi/ap_config", "w") as f:
                f.write(ap_config_content)
            
            logger.info(f"Wrote AP config: SSID={ssid}, channel={channel}, IP={ip_address}")
            
            # Restart wifi-ap.service to apply changes
            success, _ = self._run_command(["systemctl", "restart", "wifi-ap"])
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to set AP config: {e}")
            return False

