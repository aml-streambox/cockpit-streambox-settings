# cockpit-streambox-settings - D-Bus API Specification

## Service Details

| Property | Value |
|----------|-------|
| Service Name | `org.cockpit.StreamboxSettings` |
| Object Path | `/org/cockpit/StreamboxSettings` |
| Interface | `org.cockpit.StreamboxSettings1` |

---

## Methods

### Basic Settings

#### GetBasicSettings

Get current basic system settings.

| | Type | Description |
|-|------|-------------|
| **Returns** | `a{sv}` | Basic settings object |

**Example Response:**
```json
{
  "hostname": "streambox",
  "timezone": "UTC",
  "locale": "en_US.UTF-8",
  "ntp_server": "pool.ntp.org"
}
```

---

#### SetHostname

Set system hostname.

| | Type | Description |
|-|------|-------------|
| **hostname** | `s` | New hostname |
| **Returns** | `b` | Success |

---

#### SetTimezone

Set system timezone.

| | Type | Description |
|-|------|-------------|
| **timezone** | `s` | Timezone (e.g., "UTC", "America/New_York") |
| **Returns** | `b` | Success |

---

#### SetLocale

Set system locale.

| | Type | Description |
|-|------|-------------|
| **locale** | `s` | Locale (e.g., "en_US.UTF-8") |
| **Returns** | `b` | Success |

---

#### GetAvailableTimezones

Get list of available timezones.

| | Type | Description |
|-|------|-------------|
| **Returns** | `as` | Array of timezone strings |

---

#### GetAvailableLocales

Get list of available locales.

| | Type | Description |
|-|------|-------------|
| **Returns** | `as` | Array of locale strings |

---

### Network Settings

#### GetNetworkStatus

Get current network status.

| | Type | Description |
|-|------|-------------|
| **Returns** | `a{sv}` | Network status object |

**Example Response:**
```json
{
  "wired": {
    "interface": "eth0",
    "connected": true,
    "method": "dhcp",
    "ip_address": "192.168.1.100",
    "netmask": "255.255.255.0",
    "gateway": "192.168.1.1",
    "dns_servers": ["8.8.8.8", "8.8.4.4"]
  },
  "wifi_client": {
    "interface": "wlan0",
    "connected": true,
    "ssid": "MyWiFi",
    "security": "WPA2",
    "method": "dhcp",
    "ip_address": "192.168.1.101",
    "signal_strength": 85
  },
  "wifi_ap": {
    "interface": "wlan0",
    "enabled": true,
    "ssid": "StreamBox-AP",
    "security": "WPA2",
    "ip_address": "192.168.4.1",
    "dhcp_enabled": true,
    "ip_range_start": "192.168.4.100",
    "ip_range_end": "192.168.4.200"
  }
}
```

---

#### SetWiredNetwork

Configure wired network interface.

| | Type | Description |
|-|------|-------------|
| **interface** | `s` | Network interface (e.g., "eth0") |
| **method** | `s` | IP method ("dhcp" or "static") |
| **ip_address** | `s` | Optional: IP address for static |
| **netmask** | `s` | Optional: Netmask for static |
| **gateway** | `s` | Optional: Gateway for static |
| **dns_servers** | `as` | Optional: DNS servers |
| **Returns** | `b` | Success |

---

#### ScanWifiNetworks

Scan for available WiFi networks.

| | Type | Description |
|-|------|-------------|
| **Returns** | `a{sv}[]` | Array of WiFi network objects |

**Example Response:**
```json
[
  {
    "ssid": "MyWiFi",
    "bssid": "00:11:22:33:44:55",
    "security": "WPA2",
    "signal_strength": 85,
    "frequency": 2412
  },
  {
    "ssid": "OpenNetwork",
    "bssid": "00:11:22:33:44:66",
    "security": "Open",
    "signal_strength": 60,
    "frequency": 5180
  }
]
```

---

#### ConnectWifi

Connect to WiFi network as client.

| | Type | Description |
|-|------|-------------|
| **ssid** | `s` | Network SSID |
| **password** | `s` | Optional: Password for secured networks |
| **security** | `s` | Optional: Security type ("WPA2", "WPA3", "Open") |
| **method** | `s` | Optional: IP method ("dhcp" or "static") |
| **ip_address** | `s` | Optional: IP address for static |
| **netmask** | `s` | Optional: Netmask for static |
| **gateway** | `s` | Optional: Gateway for static |
| **dns_servers** | `as` | Optional: DNS servers |
| **Returns** | `b` | Success |

---

#### DisconnectWifi

Disconnect from WiFi network.

| | Type | Description |
|-|------|-------------|
| **Returns** | `b` | Success |

---

#### SetWifiAp

Configure WiFi Access Point.

| | Type | Description |
|-|------|-------------|
| **enabled** | `b` | Enable/disable AP |
| **ssid** | `s` | AP SSID |
| **password** | `s` | Optional: Password |
| **security** | `s` | Optional: Security type ("WPA2", "WPA3", "Open") |
| **dhcp_enabled** | `b` | Enable DHCP server |
| **ip_address** | `s` | Optional: AP IP address |
| **ip_range_start** | `s` | Optional: DHCP range start |
| **ip_range_end** | `s` | Optional: DHCP range end |
| **Returns** | `b` | Success |

---

#### GetWifiApStatus

Get current WiFi AP status.

| | Type | Description |
|-|------|-------------|
| **Returns** | `a{sv}` | AP status object |

**Example Response:**
```json
{
  "enabled": true,
  "ssid": "StreamBox-AP",
  "security": "WPA2",
  "ip_address": "192.168.4.1",
  "dhcp_enabled": true,
  "connected_clients": 2
}
```

---

### TVServer Settings

#### GetTvserverConfig

Get current tvserver configuration.

| | Type | Description |
|-|------|-------------|
| **Returns** | `s` | JSON configuration string |

**Example Response:**
```json
{
  "video": {
    "game_mode": 2,
    "vrr_mode": 2,
    "hdmi_source": "HDMI2"
  },
  "audio": {
    "enabled": true,
    "capture_device": "hw:0,2",
    "playback_device": "hw:0,0",
    "latency_us": 20000,
    "sample_format": "S16_LE",
    "channels": 2,
    "sample_rate": 48000
  },
  "hdcp": {
    "enabled": false,
    "version": "auto"
  },
  "debug": {
    "trace_level": 0
  }
}
```

---

#### SetTvserverConfig

Set tvserver configuration.

| | Type | Description |
|-|------|-------------|
| **config_json** | `s` | JSON configuration string |
| **Returns** | `b` | Success |

---

#### ReloadTvserverConfig

Reload tvserver configuration (triggers SIGHUP).

| | Type | Description |
|-|------|-------------|
| **Returns** | `b` | Success |

---

#### GetVideoSettings

Get video settings from tvserver config.

| | Type | Description |
|-|------|-------------|
| **Returns** | `a{sv}` | Video settings object |

**Example Response:**
```json
{
  "game_mode": 2,
  "game_mode_options": [
    {"value": 0, "label": "Disabled"},
    {"value": 1, "label": "Mode 1"},
    {"value": 2, "label": "Mode 2 + VRR"}
  ],
  "vrr_mode": 2,
  "vrr_mode_options": [
    {"value": 0, "label": "Force VRR"},
    {"value": 1, "label": "VRR on (EDID)"},
    {"value": 2, "label": "Auto"}
  ],
  "hdmi_source": "HDMI2",
  "hdmi_source_options": ["HDMI1", "HDMI2", "HDMI3", "HDMI4"]
}
```

---

#### SetVideoSettings

Set video settings.

| | Type | Description |
|-|------|-------------|
| **game_mode** | `i` | Game mode (0=disabled, 1=mode1, 2=mode2+VRR) |
| **vrr_mode** | `i` | VRR mode (0=force VRR, 1=VRR on (EDID), 2=auto) |
| **hdmi_source** | `s` | HDMI source ("HDMI1"-"HDMI4") |
| **Returns** | `b` | Success |

---

#### GetAudioSettings

Get audio settings from tvserver config.

| | Type | Description |
|-|------|-------------|
| **Returns** | `a{sv}` | Audio settings object |

**Example Response:**
```json
{
  "enabled": true,
  "capture_device": "hw:0,2",
  "playback_device": "hw:0,0",
  "latency_us": 20000,
  "sample_format": "S16_LE",
  "sample_format_options": ["S16_LE", "S32_LE", "FLOAT_LE"],
  "channels": 2,
  "sample_rate": 48000,
  "sample_rate_options": [44100, 48000, 96000]
}
```

---

#### SetAudioSettings

Set audio settings.

| | Type | Description |
|-|------|-------------|
| **enabled** | `b` | Enable audio passthrough |
| **capture_device** | `s` | ALSA capture device |
| **playback_device** | `s` | ALSA playback device |
| **latency_us** | `i` | Latency in microseconds (1000-100000) |
| **sample_format** | `s` | Sample format |
| **channels** | `i` | Channel count (1-8) |
| **sample_rate** | `i` | Sample rate (e.g., 48000) |
| **Returns** | `b` | Success |

---

#### GetHdcpSettings

Get HDCP settings from tvserver config.

| | Type | Description |
|-|------|-------------|
| **Returns** | `a{sv}` | HDCP settings object |

**Example Response:**
```json
{
  "enabled": false,
  "version": "auto",
  "version_options": ["auto", "1.4", "2.2"]
}
```

---

#### SetHdcpSettings

Set HDCP settings.

| | Type | Description |
|-|------|-------------|
| **enabled** | `b` | Enable HDCP |
| **version** | `s` | HDCP version ("auto", "1.4", "2.2") |
| **Returns** | `b` | Success |

---

#### GetDebugSettings

Get debug settings from tvserver config.

| | Type | Description |
|-|------|-------------|
| **Returns** | `a{sv}` | Debug settings object |

**Example Response:**
```json
{
  "trace_level": 0,
  "trace_level_options": [
    {"value": 0, "label": "Disabled"},
    {"value": 1, "label": "Basic"},
    {"value": 2, "label": "Verbose"},
    {"value": 3, "label": "Debug"}
  ]
}
```

---

#### SetDebugSettings

Set debug settings.

| | Type | Description |
|-|------|-------------|
| **trace_level** | `i` | Trace level (0-3) |
| **Returns** | `b` | Success |

---

### Storage Settings

#### GetStorageDevices

Get list of storage devices.

| | Type | Description |
|-|------|-------------|
| **Returns** | `a{sv}[]` | Array of storage device objects |

**Example Response:**
```json
[
  {
    "name": "/dev/mmcblk0",
    "label": "SDCard",
    "size_gb": 32.0,
    "type": "sdcard",
    "mounted": true,
    "mount_point": "/mnt/sdcard",
    "filesystem": "ext4",
    "used_gb": 15.5,
    "available_gb": 16.5
  },
  {
    "name": "/dev/sda1",
    "label": "USB Drive",
    "size_gb": 128.0,
    "type": "usb",
    "mounted": false,
    "mount_point": null,
    "filesystem": "ntfs",
    "used_gb": 0,
    "available_gb": 128.0
  }
]
```

---

#### MountStorage

Mount storage device.

| | Type | Description |
|-|------|-------------|
| **device** | `s` | Device path (e.g., "/dev/mmcblk0") |
| **mount_point** | `s` | Optional: Mount point (default: auto) |
| **Returns** | `b` | Success |

---

#### UnmountStorage

Unmount storage device.

| | Type | Description |
|-|------|-------------|
| **device** | `s` | Device path (e.g., "/dev/mmcblk0") |
| **Returns** | `b` | Success |

---

#### FormatStorage

Format storage device.

| | Type | Description |
|-|------|-------------|
| **device** | `s` | Device path (e.g., "/dev/mmcblk0") |
| **filesystem** | `s` | Filesystem type ("ext4", "vfat", "ntfs") |
| **label** | `s` | Optional: Volume label |
| **Returns** | `b` | Success |

---

#### GetStorageInfo

Get detailed information about storage device.

| | Type | Description |
|-|------|-------------|
| **device** | `s` | Device path |
| **Returns** | `a{sv}` | Storage info object |

**Example Response:**
```json
{
  "name": "/dev/mmcblk0",
  "label": "SDCard",
  "size_gb": 32.0,
  "type": "sdcard",
  "mounted": true,
  "mount_point": "/mnt/sdcard",
  "filesystem": "ext4",
  "used_gb": 15.5,
  "available_gb": 16.5,
  "used_percent": 48.4,
  "block_size": 4096,
  "model": "SD32G",
  "serial": "1234567890ABC"
}
```

---

### System Status

#### GetSystemStatus

Get overall system status.

| | Type | Description |
|-|------|-------------|
| **Returns** | `a{sv}` | System status object |

**Example Response:**
```json
{
  "hostname": "streambox",
  "uptime": 3600,
  "load_average": [0.5, 0.3, 0.2],
  "memory_used_mb": 512,
  "memory_total_mb": 2048,
  "cpu_usage_percent": 15.5,
  "disk_used_gb": 8.5,
  "disk_total_gb": 32.0,
  "tvservice_running": true,
  "streambox_settings_running": true
}
```

---

#### GetHardwareInfo

Get hardware information.

| | Type | Description |
|-|------|-------------|
| **Returns** | `a{sv}` | Hardware info object |

**Example Response:**
```json
{
  "soc": "A311D2",
  "kernel_version": "5.15.0",
  "firmware_version": "1.0.0",
  "serial_number": "ABC123456",
  "mac_address": "00:11:22:33:44:55"
}
```

---

### Configuration Management

#### GetConfig

Get current system configuration.

| | Type | Description |
|-|------|-------------|
| **Returns** | `s` | JSON configuration string |

---

#### SetConfig

Set system configuration.

| | Type | Description |
|-|------|-------------|
| **config_json** | `s` | JSON configuration string |
| **Returns** | `b` | Success |

---

#### ExportConfig

Export configuration to file.

| | Type | Description |
|-|------|-------------|
| **profile_name** | `s` | Profile name |
| **Returns** | `s` | Exported configuration JSON |

---

#### ImportConfig

Import configuration from file.

| | Type | Description |
|-|------|-------------|
| **config_json** | `s` | JSON configuration string |
| **apply** | `b` | Apply configuration immediately |
| **Returns** | `b` | Success |

---

#### GetProfiles

List available configuration profiles.

| | Type | Description |
|-|------|-------------|
| **Returns** | `as` | Array of profile names |

---

#### LoadProfile

Load configuration profile.

| | Type | Description |
|-|------|-------------|
| **profile_name** | `s` | Profile name |
| **Returns** | `b` | Success |

---

#### SaveProfile

Save current configuration as profile.

| | Type | Description |
|-|------|-------------|
| **profile_name** | `s` | Profile name |
| **Returns** | `b` | Success |

---

#### DeleteProfile

Delete configuration profile.

| | Type | Description |
|-|------|-------------|
| **profile_name** | `s` | Profile name |
| **Returns** | `b` | Success |

---

## Signals

#### BasicSettingsChanged

Emitted when basic settings change.

| | Type | Description |
|-|------|-------------|
| **settings** | `a{sv}` | New settings object |

---

#### NetworkStatusChanged

Emitted when network status changes.

| | Type | Description |
|-|------|-------------|
| **status** | `a{sv}` | New status object |

---

#### WifiNetworksChanged

Emitted when WiFi networks list changes.

| | Type | Description |
|-|------|-------------|
| **networks** | `a{sv}[]` | Array of WiFi network objects |

---

#### TvserverConfigChanged

Emitted when tvserver configuration changes.

| | Type | Description |
|-|------|-------------|
| **config** | `s` | New configuration JSON |

---

#### StorageDevicesChanged

Emitted when storage devices change.

| | Type | Description |
|-|------|-------------|
| **devices** | `a{sv}[]` | Array of storage device objects |

---

#### SystemStatusChanged

Emitted when system status changes.

| | Type | Description |
|-|------|-------------|
| **status** | `a{sv}` | New status object |

---

## Error Codes

| Code | Description |
|------|-------------|
| `InvalidHostname` | Invalid hostname format |
| `InvalidTimezone` | Invalid timezone |
| `InvalidLocale` | Invalid locale |
| `NetworkError` | Network operation failed |
| `WifiConnectFailed` | WiFi connection failed |
| `WifiScanFailed` | WiFi scan failed |
| `InvalidIpConfig` | Invalid IP configuration |
| `TvserverConfigError` | tvserver configuration error |
| `InvalidGameMode` | Invalid game mode value |
| `InvalidVrrMode` | Invalid VRR mode value |
| `InvalidHdmiSource` | Invalid HDMI source |
| `InvalidAudioDevice` | Invalid audio device |
| `InvalidLatency` | Invalid latency value |
| `InvalidSampleRate` | Invalid sample rate |
| `InvalidHdcpVersion` | Invalid HDCP version |
| `StorageDeviceNotFound` | Storage device not found |
| `StorageMountFailed` | Storage mount failed |
| `StorageUnmountFailed` | Storage unmount failed |
| `StorageFormatFailed` | Storage format failed |
| `InvalidFilesystem` | Invalid filesystem type |
| `ProfileNotFound` | Configuration profile not found |
| `ProfileExists` | Configuration profile already exists |
| `InvalidConfig` | Configuration validation failed |
| `PermissionDenied` | Permission denied |
| `OperationFailed` | General operation failure |
