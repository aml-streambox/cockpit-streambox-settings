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

```bash
# On target device
systemctl start streambox-settings
# Access via Cockpit at https://<device-ip>:9090
```

## Requirements

- Amlogic A311D2/T7 Streambox hardware
- Yocto-built image with Cockpit
- tvservice (aml_tvserver_streambox) running

## License

MIT
