# cockpit-streambox-settings

A Cockpit plugin for managing system settings on Amlogic A311D2 (T6/T7) Streambox.

## Platform

| Component | Version |
|-----------|---------|
| SoC | Amlogic A311D2 |
| Cockpit | 220 (PatternFly 4) |
| Python | 3.10+ |

## Features

- **Basic Settings** - Device name, timezone, system locale
- **Network Settings** - Wired, WiFi client, WiFi AP configuration
- **TVServer Settings** - Video, audio, HDCP, debug configuration
- **Storage Settings** - SDCard management, formatting, mount points

## Documentation

See [doc/implementation_plan/](doc/implementation_plan/) for:

- [Overview](doc/implementation_plan/overview.md) - Architecture and phases
- [API Specification](doc/implementation_plan/api.md) - D-Bus interface
- [TVServer Config Reference](doc/implementation_plan/hardware_reference.md) - tvserver configuration
- [Operations](doc/implementation_plan/operations.md) - Debugging and logs

## Quick Start

### Direct Installation (A311D2 Yocto Linux)

```bash
# On target device, navigate to project directory
cd /path/to/cockpit-streambox-settings

# Run installation script
sudo ./install.sh

# Access via Cockpit at https://<device-ip>:9090
```

### Troubleshooting D-Bus Connection

If you see "Failed to connect to D-Bus service" errors:

```bash
# Run diagnostic script
sudo ./diagnose-dbus.sh

# Check service logs
journalctl -u streambox-settings.service -f

# Verify D-Bus registration
busctl --system list | grep Streambox

# Check if Python dependencies are installed
opkg list-installed | grep python3
```

### Required Python Dependencies

Ensure these packages are installed:

```bash
opkg install python3-dbus python3-pygobject python3-asyncio python3-glib
```

### Yocto Build

```bash
# Add recipe to your Yocto layer
bitbake cockpit-streambox-settings

# Install package on target
opkg install cockpit-streambox-settings
```

### Manual Installation

```bash
# Install backend
mkdir -p /usr/lib/streambox-settings
cp backend/*.py /usr/lib/streambox-settings/
chmod +x /usr/lib/streambox-settings/main.py

# Install frontend
mkdir -p /usr/share/cockpit/streambox-settings
cp frontend/* /usr/share/cockpit/streambox-settings/

# Install service
cp yocto/files/streambox-settings.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable streambox-settings
systemctl start streambox-settings
```

## Requirements

- Amlogic A311D2/T7 Streambox hardware
- Yocto-built image with Cockpit
- tvservice (aml_tvserver_streambox) running

## License

MIT
