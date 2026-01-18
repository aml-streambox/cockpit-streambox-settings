# cockpit-streambox-settings - Implementation Overview

## Project Summary

A Cockpit plugin for Amlogic A311D2 (T6) Streambox that manages system settings through four main tabs: Basic Settings, Network Settings, TVServer Settings, and Storage Settings.

### Key Features

| Feature | Description |
|---------|-------------|
| Basic Settings | Device name (hostname), timezone, system locale |
| Network Settings | Wired network, WiFi client, WiFi AP configuration |
| TVServer Settings | Video, audio, HDCP, debug configuration from tvserver |
| Storage Settings | SDCard management, formatting, mount points |

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3 + asyncio |
| Frontend | Vanilla JS + cockpit.js |
| UI Theme | Cockpit native (PatternFly) |
| IPC | D-Bus |
| Process Mgmt | systemd |
| Hardware Interface | tvserver config file (`/etc/streambox-tv/config.json`) |
| Network Interface | NetworkManager / wpa_supplicant |
| Storage Interface | udev / mount |
| Config | JSON files |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cockpit Web UI                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Basic        │ │ Network      │ │ TVServer             │ │
│  │ Settings     │ │ Settings     │ │ Settings             │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
│  ┌──────────────┐                                        │
│  │ Storage      │                                        │
│  │ Settings     │                                        │
│  └──────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
                           │ D-Bus
┌─────────────────────────────────────────────────────────────┐
│              streambox-settings Daemon                     │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │
│  │ Basic      │ │ Network    │ │ TVServer   │ │ Storage │ │
│  │ Manager    │ │ Manager    │ │ Manager    │ │ Manager │ │
│  └───────────┘ └───────────┘ └───────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│              System Services & Hardware                   │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │
│  │ Network    │ │ tvserver   │ │ Storage    │ │ System  │ │
│  │ Manager    │ │ config     │ │ Devices   │ │ Config  │ │
│  └───────────┘ └───────────┘ └───────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
cockpit-streambox-settings/
├── README.md
├── LICENSE
├── doc/
│   └── implementation_plan/
│       ├── overview.md              # This file
│       ├── guidelines.md            # Project rules
│       ├── api.md                 # D-Bus API spec
│       ├── hardware_reference.md    # tvserver config reference
│       └── operations.md           # Debugging, logs, diagnostics
├── backend/
│   ├── main.py                   # Entry point
│   ├── basic.py                  # Basic settings (hostname, timezone)
│   ├── network.py                # Network settings (wired, WiFi)
│   ├── tvserver.py               # TVServer config management
│   ├── storage.py                # Storage management (SDCard)
│   ├── config.py                 # Configuration management
│   └── api.py                   # D-Bus interface
├── frontend/
│   ├── manifest.json              # Cockpit metadata
│   ├── index.html                # Entry point
│   ├── streambox-settings.js     # Main logic
│   ├── basic-settings.js         # Basic settings UI
│   ├── network-settings.js       # Network settings UI
│   ├── tvserver-settings.js     # TVServer settings UI
│   ├── storage-settings.js       # Storage settings UI
│   └── streambox-settings.css   # Styling
├── yocto/
│   ├── cockpit-streambox-settings_1.0.bb
│   └── files/
│       └── streambox-settings.service
└── tests/
    ├── conftest.py
    ├── unit/
    └── integration/
```

---

## Runtime Layout

```
/usr/lib/streambox-settings/        # Backend Python
/usr/share/cockpit/streambox-settings/  # Frontend
/var/lib/streambox-settings/
├── config.json                  # System settings
└── profiles/                   # Configuration profiles
    └── {profile-name}.json
/etc/streambox-tv/
└── config.json                  # tvserver configuration (managed by tvservice)
```

---

## UI Tabs Structure

### 1. Basic Settings Tab

**Fields:**
- Device Name (hostname)
- Timezone
- System Locale
- (Optional) NTP server settings
- (Optional) Keyboard layout

**System Commands:**
- `hostnamectl` - Set hostname
- `timedatectl` - Set timezone
- `localectl` - Set locale

### 2. Network Settings Tab

**Sub-tabs:**
- Wired Network
- WiFi Client
- WiFi AP

**Wired Network:**
- Interface selection (eth0, eth1, etc.)
- IP configuration (DHCP/Static)
- Static IP fields: IP address, netmask, gateway
- DNS settings

**WiFi Client:**
- Network scanning
- Network selection
- Security type (WPA2, WPA3, Open)
- Password input
- IP configuration (DHCP/Static)
- DNS settings

**WiFi AP:**
- AP name (SSID)
- Password
- Security type
- DHCP server settings
- IP range configuration

**System Commands:**
- `nmcli` - NetworkManager CLI
- `wpa_supplicant` - WiFi client
- `hostapd` - WiFi AP
- `dnsmasq` - DHCP/DNS server

### 3. TVServer Settings Tab

**Exposes tvserver config.json fields:**

**Video Section:**
- Game Mode (0=disabled, 1=mode1, 2=mode2+VRR)
- VRR Mode (0=force VRR, 1=VRR on (EDID), 2=auto)
- HDMI Source ("HDMI1"-"HDMI4")

**Audio Section:**
- Audio Passthrough (enabled/disabled)
- Capture Device (ALSA device, e.g., "hw:0,2")
- Playback Device (ALSA device, e.g., "hw:0,0")
- Latency (microseconds, 1000-100000)
- Sample Format (e.g., "S16_LE")
- Channels (1-8)
- Sample Rate (e.g., 48000)

**HDCP Section:**
- HDCP Enabled (true/false)
- HDCP Version ("auto", "1.4", "2.2")

**Debug Section:**
- Trace Level (0-3)

**File Location:** `/etc/streambox-tv/config.json`
**Reload Method:** SIGHUP to tvservice or inotify watch

### 4. Storage Settings Tab

**SDCard Management:**
- Device detection
- Mount point display
- Format functionality
- Unmount functionality
- Storage usage display

**System Commands:**
- `lsblk` - List block devices
- `mount` - Mount filesystem
- `umount` - Unmount filesystem
- `mkfs.*` - Format filesystem
- `df` - Disk usage

---

## Implementation Phases

### Phase 1: Core (Priority: High)
- [ ] Backend skeleton with D-Bus server
- [ ] Basic Settings tab (hostname, timezone, locale)
- [ ] Basic Cockpit UI with tab navigation
- [ ] Yocto recipe + systemd service

### Phase 2: Network Settings
- [ ] Wired network configuration
- [ ] WiFi client scanning and configuration
- [ ] WiFi AP configuration
- [ ] Network status monitoring

### Phase 3: TVServer Settings
- [ ] TVServer config file parsing
- [ ] Video settings UI (Game Mode, VRR, HDMI Source)
- [ ] Audio settings UI (Passthrough, devices, latency)
- [ ] HDCP settings UI
- [ ] Debug settings UI
- [ ] Config reload mechanism

### Phase 4: Storage Settings
- [ ] SDCard detection and display
- [ ] Mount/unmount functionality
- [ ] Format functionality
- [ ] Storage usage display

### Phase 5: Advanced Features
- [ ] Configuration profiles
- [ ] Import/Export functionality
- [ ] System diagnostics
- [ ] Log viewing

---

## Memory Budget

Target: <100MB for daemon

| Component | Estimated RAM |
|-----------|---------------|
| Cockpit core | ~80 MB |
| streambox-settings daemon | ~30-50 MB |
| **Total** | **~110-130 MB** |

---

## Related Documents

- [guidelines.md](./guidelines.md) - Coding standards, git workflow
- [api.md](./api.md) - D-Bus API specification
- [hardware_reference.md](./hardware_reference.md) - tvserver config reference
- [operations.md](./operations.md) - Debugging and diagnostics
