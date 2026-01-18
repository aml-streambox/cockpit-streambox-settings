# cockpit-streambox-settings - Project Guidelines

## Code Standards

### Python (Backend)

- **Version:** Python 3.8+
- **Style:** PEP 8
- **Type hints:** Required for public functions
- **Docstrings:** Google style

```python
def set_hostname(hostname: str) -> bool:
    """Set system hostname.

    Args:
        hostname: New hostname string.

    Returns:
        True if set successfully, False otherwise.
    """
```

### JavaScript (Frontend)

- **Style:** ES6+, no TypeScript (keep it simple for embedded)
- **No frameworks:** Vanilla JS + cockpit.js only
- **Naming:** camelCase for functions, UPPER_CASE for constants

```javascript
const REFRESH_INTERVAL = 5000;

function updateBasicSettings() {
    // ...
}
```

### CSS

- **Framework:** PatternFly 4 (Cockpit native)
- **Custom styles:** Prefix with `sbs-` (e.g., `.sbs-settings-card`)
- **Avoid:** Inline styles, !important

---

## Git Workflow

### Branches

| Branch | Purpose |
|--------|---------|
| `main` | Stable releases |
| `dev` | Development integration |
| `feature/*` | New features |
| `fix/*` | Bug fixes |

### Commit Messages

Format: `<type>: <description>`

Types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Build/config changes

Example:
```
feat: add WiFi AP configuration
fix: handle network disconnect gracefully
docs: update API specification
```

---

## File Naming

| Type | Convention | Example |
|------|------------|---------|
| Python modules | snake_case | `basic.py` |
| JavaScript | kebab-case | `basic-settings.js` |
| Documentation | kebab-case | `api-spec.md` |
| Config files | lowercase | `config.json` |

---

## Configuration Files

### System Configuration JSON

**Location:** `/var/lib/streambox-settings/config.json`

Required fields:
```json
{
  "basic": {
    "hostname": "streambox",
    "timezone": "UTC",
    "locale": "en_US.UTF-8"
  },
  "network": {
    "wired": {
      "interface": "eth0",
      "method": "dhcp"
    },
    "wifi_client": {
      "interface": "wlan0",
      "ssid": null,
      "method": "dhcp"
    },
    "wifi_ap": {
      "enabled": false,
      "ssid": "StreamBox-AP",
      "dhcp_enabled": true
    }
  }
}
```

### tvserver Configuration JSON

**Location:** `/etc/streambox-tv/config.json` (managed by tvservice)

Required fields:
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

### Profile JSON

```json
{
  "name": "Gaming Profile",
  "description": "Optimized for gaming",
  "config": {
    "basic": {
      "hostname": "streambox-gaming"
    },
    "tvserver": {
      "video": {
        "game_mode": 2,
        "vrr_mode": 2
      }
    }
  }
}
```

---

## Error Handling

### Backend

- Use exceptions for errors
- Log all errors with context
- Return structured error responses via D-Bus

```python
import logging

logger = logging.getLogger(__name__)

try:
    set_hostname(hostname)
except HostnameError as e:
    logger.error(f"Failed to set hostname: {e}")
    raise DBusError("InvalidHostname", str(e))
```

### Frontend

- Show user-friendly error messages
- Log details to console for debugging
- Use Cockpit's notification system

```javascript
cockpit.spawn(["hostnamectl", "set-hostname", newHostname])
    .fail(function(error) {
        console.error("Set hostname failed:", error);
        showNotification("error", "Failed to set hostname");
    });
```

---

## Security Rules

1. **System commands:** Only root can modify system settings
2. **No shell injection:** Always use arrays for subprocess calls
3. **Validate inputs:** Check hostnames, IPs, paths before use
4. **D-Bus auth:** Cockpit handles authentication
5. **WiFi passwords:** Never log WiFi passwords

```python
# GOOD
subprocess.run(["hostnamectl", "set-hostname", hostname])

# BAD - shell injection risk
subprocess.run(f"hostnamectl set-hostname {hostname}", shell=True)
```

---

## Testing

### Unit Tests

Location: `tests/`

```bash
python -m pytest tests/
```

### Manual Testing

1. Build Yocto image with recipe
2. Deploy to target hardware
3. Access Cockpit at `https://<device-ip>:9090`
4. Navigate to Streambox Settings
5. Test each tab:
   - Basic Settings: Change hostname, timezone
   - Network Settings: Configure wired, WiFi client, WiFi AP
   - TVServer Settings: Modify video, audio, HDCP settings
   - Storage Settings: Format, mount/unmount SDCard

---

## Dependencies

### Runtime

| Package | Purpose |
|---------|---------|
| python3 | Backend runtime |
| python3-dbus | D-Bus bindings |
| cockpit | Web interface |
| NetworkManager | Network management |
| wpa_supplicant | WiFi client |
| hostapd | WiFi AP |
| dnsmasq | DHCP/DNS server |
| udisks2 | Storage management |

### Development

| Package | Purpose |
|---------|---------|
| pytest | Unit testing |
| pylint | Linting |

---

## Memory Guidelines

**Target:** <100MB for daemon

- Avoid loading entire files into memory
- Stream large responses
- Clean up subprocess handles
- Limit configuration files in memory

---

## System Integration

### Basic Settings

**System Commands:**
- `hostnamectl` - Set/get hostname
- `timedatectl` - Set timezone
- `localectl` - Set locale

**File Locations:**
- `/etc/hostname` - System hostname
- `/etc/localtime` - Timezone symlink
- `/etc/locale.conf` - Locale configuration

### Network Settings

**NetworkManager CLI:**
- `nmcli` - Network configuration
- `nmcli device` - Device management
- `nmcli connection` - Connection management

**WiFi Client:**
- `wpa_supplicant` - WiFi client daemon
- Configuration: `/etc/wpa_supplicant/wpa_supplicant.conf`

**WiFi AP:**
- `hostapd` - WiFi AP daemon
- Configuration: `/etc/hostapd/hostapd.conf`
- `dnsmasq` - DHCP/DNS server

**Network Files:**
- `/etc/NetworkManager/system-connections/` - Connection profiles
- `/etc/resolv.conf` - DNS configuration
- `/etc/hosts` - Hosts file

### TVServer Settings

**tvservice Integration:**
- Configuration file: `/etc/streambox-tv/config.json`
- Reload mechanism: SIGHUP or inotify watch
- Service: `tvservice` (aml_tvserver_streambox)

**Configuration Sections:**
- **Video:** Game Mode, VRR Mode, HDMI Source
- **Audio:** Passthrough, devices, latency, format
- **HDCP:** Enable/disable, version
- **Debug:** Trace level

### Storage Settings

**Storage Commands:**
- `lsblk` - List block devices
- `mount` - Mount filesystem
- `umount` - Unmount filesystem
- `mkfs.*` - Format filesystem
- `df` - Disk usage
- `udisksctl` - Storage management via udisks2

**Storage Files:**
- `/etc/fstab` - Mount points
- `/dev/` - Block devices
- `/run/media/` - Auto-mount points

---

## UI Guidelines

### Tab Structure

The plugin uses four main tabs:

1. **Basic Settings** - System hostname, timezone, locale
2. **Network Settings** - Wired, WiFi client, WiFi AP (sub-tabs)
3. **TVServer Settings** - Video, audio, HDCP, debug
4. **Storage Settings** - SDCard management

### PatternFly Components

- Use PatternFly 4 components for consistency
- Follow Cockpit design patterns
- Ensure responsive design
- Support both English and Chinese

### User Experience

- Provide clear feedback for all operations
- Show loading states for long operations (formatting, WiFi scanning)
- Display error messages prominently
- Allow configuration preview before applying
- Warn before destructive operations (formatting)

### Form Validation

- Validate hostname format (alphanumeric, hyphens, dots)
- Validate IP addresses (IPv4/IPv6)
- Validate timezone (from available list)
- Validate locale (from available list)
- Validate WiFi passwords (minimum length)

---

## Performance Considerations

- Minimize D-Bus calls
- Cache network status when appropriate
- Use efficient data structures
- Avoid blocking main thread
- Implement debouncing for rapid status changes
- Lazy load WiFi network lists
- Cache tvserver configuration

---

## Adding New Features

1. Create issue/task describing feature
2. Update `overview.md` if architecture changes
3. Update `api.md` if D-Bus interface changes
4. Implement with tests
5. Update README if user-facing
6. Update `hardware_reference.md` if tvserver config changes

---

## Backend Module Structure

### basic.py

Manages basic system settings:
- Hostname management
- Timezone management
- Locale management
- System time settings

### network.py

Manages network configuration:
- Wired network setup
- WiFi client configuration
- WiFi AP configuration
- Network status monitoring
- WiFi scanning

### tvserver.py

Manages tvserver configuration:
- Read/write config.json
- Parse video, audio, HDCP, debug settings
- Trigger config reload (SIGHUP)
- Validate configuration values

### storage.py

Manages storage devices:
- Device detection
- Mount/unmount operations
- Format operations
- Storage usage monitoring

### config.py

Manages system configuration:
- Load/save config.json
- Profile management
- Configuration validation
- Import/export functionality

### api.py

D-Bus interface:
- Method definitions
- Signal emission
- Error handling
- Type conversion
