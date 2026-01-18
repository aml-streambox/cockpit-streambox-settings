# cockpit-streambox-settings - TVServer Configuration Reference

This document describes the tvserver configuration file structure and available settings.

## Overview

The tvserver (aml_tvserver_streambox) manages HDMI RX to TX passthrough functionality through a JSON configuration file located at `/etc/streambox-tv/config.json`.

## Configuration File Structure

### Complete Configuration

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

## Video Settings

### Game Mode

Controls video processing optimization for gaming.

**Field:** `video.game_mode`
**Type:** Integer
**Values:**
- `0` - Disabled
- `1` - Mode 1
- `2` - Mode 2 + VRR (default)

**Description:**
- Disabled: No game mode optimization
- Mode 1: Basic game mode optimization
- Mode 2 + VRR: Advanced game mode with VRR enabled

**Example:**
```json
{
  "video": {
    "game_mode": 2
  }
}
```

### VRR Mode

Controls Variable Refresh Rate behavior.

**Field:** `video.vrr_mode`
**Type:** Integer
**Values:**
- `0` - Force VRR
- `1` - VRR on (EDID)
- `2` - Auto (default)

**Description:**
- Force VRR: Always enable VRR regardless of EDID
- VRR on (EDID): Enable VRR only if EDID supports it
- Auto: Automatically determine VRR mode based on source

**Example:**
```json
{
  "video": {
    "vrr_mode": 2
  }
}
```

### HDMI Source

Selects which HDMI input port to use.

**Field:** `video.hdmi_source`
**Type:** String
**Values:**
- `"HDMI1"` - HDMI input port 1
- `"HDMI2"` - HDMI input port 2 (default)
- `"HDMI3"` - HDMI input port 3
- `"HDMI4"` - HDMI input port 4

**Description:**
Specifies which HDMI input port should be used as the video source for passthrough.

**Example:**
```json
{
  "video": {
    "hdmi_source": "HDMI2"
  }
}
```

---

## Audio Settings

### Audio Passthrough

Enables or disables audio passthrough from HDMI RX to HDMI TX.

**Field:** `audio.enabled`
**Type:** Boolean
**Values:**
- `true` - Enable audio passthrough (default)
- `false` - Disable audio passthrough

**Description:**
When enabled, audio from the selected HDMI input is passed through to the HDMI output without processing.

**Example:**
```json
{
  "audio": {
    "enabled": true
  }
}
```

### Capture Device

ALSA device for audio capture from HDMI RX.

**Field:** `audio.capture_device`
**Type:** String
**Default:** `"hw:0,2"`
**Values:**
- `"hw:0,0"` - ALSA device 0, subdevice 0
- `"hw:0,1"` - ALSA device 0, subdevice 1
- `"hw:0,2"` - ALSA device 0, subdevice 2 (default)
- `"hw:1,0"` - ALSA device 1, subdevice 0

**Description:**
Specifies the ALSA capture device to use for reading audio from the HDMI input.

**Example:**
```json
{
  "audio": {
    "capture_device": "hw:0,2"
  }
}
```

### Playback Device

ALSA device for audio playback to HDMI TX.

**Field:** `audio.playback_device`
**Type:** String
**Default:** `"hw:0,0"`
**Values:**
- `"hw:0,0"` - ALSA device 0, subdevice 0 (default)
- `"hw:0,1"` - ALSA device 0, subdevice 1
- `"hw:1,0"` - ALSA device 1, subdevice 0

**Description:**
Specifies the ALSA playback device to use for sending audio to the HDMI output.

**Example:**
```json
{
  "audio": {
    "playback_device": "hw:0,0"
  }
}
```

### Latency

Audio latency in microseconds.

**Field:** `audio.latency_us`
**Type:** Integer
**Default:** `10000` (10ms)
**Range:** `1000` - `100000` (1ms - 100ms)
**Values:**
- `1000` - 1ms latency (minimum)
- `10000` - 10ms latency (default)
- `20000` - 20ms latency
- `50000` - 50ms latency
- `100000` - 100ms latency (maximum)

**Description:**
Controls the audio buffer latency. Lower values reduce latency but may cause audio glitches if too low.

**Example:**
```json
{
  "audio": {
    "latency_us": 20000
  }
}
```

### Sample Format

Audio sample format.

**Field:** `audio.sample_format`
**Type:** String
**Default:** `"S16_LE"`
**Values:**
- `"S16_LE"` - Signed 16-bit little-endian (default)
- `"S32_LE"` - Signed 32-bit little-endian
- `"FLOAT_LE"` - 32-bit float little-endian

**Description:**
Specifies the audio sample format for capture and playback.

**Example:**
```json
{
  "audio": {
    "sample_format": "S16_LE"
  }
}
```

### Channels

Number of audio channels.

**Field:** `audio.channels`
**Type:** Integer
**Default:** `2`
**Range:** `1` - `8`
**Values:**
- `1` - Mono
- `2` - Stereo (default)
- `6` - 5.1 surround
- `8` - 7.1 surround

**Description:**
Specifies the number of audio channels to use.

**Example:**
```json
{
  "audio": {
    "channels": 2
  }
}
```

### Sample Rate

Audio sample rate in Hz.

**Field:** `audio.sample_rate`
**Type:** Integer
**Default:** `48000`
**Values:**
- `44100` - 44.1 kHz
- `48000` - 48 kHz (default)
- `96000` - 96 kHz

**Description:**
Specifies the audio sample rate for capture and playback.

**Example:**
```json
{
  "audio": {
    "sample_rate": 48000
  }
}
```

---

## HDCP Settings

### HDCP Enabled

Enables or disables HDCP (High-bandwidth Digital Content Protection).

**Field:** `hdcp.enabled`
**Type:** Boolean
**Values:**
- `true` - Enable HDCP
- `false` - Disable HDCP (default)

**Description:**
When enabled, HDCP protection is applied to the HDMI input. This is required for some protected content.

**Example:**
```json
{
  "hdcp": {
    "enabled": false
  }
}
```

### HDCP Version

HDCP version to use.

**Field:** `hdcp.version`
**Type:** String
**Default:** `"auto"`
**Values:**
- `"auto"` - Automatically select version (default)
- `"1.4"` - HDCP 1.4
- `"2.2"` - HDCP 2.2

**Description:**
Specifies which HDCP version to use. Auto mode will negotiate the best available version.

**Example:**
```json
{
  "hdcp": {
    "version": "auto"
  }
}
```

---

## Debug Settings

### Trace Level

Debug trace level for logging.

**Field:** `debug.trace_level`
**Type:** Integer
**Default:** `0`
**Range:** `0` - `3`
**Values:**
- `0` - Disabled (default)
- `1` - Basic
- `2` - Verbose
- `3` - Debug

**Description:**
Controls the verbosity of debug logging. Higher levels produce more detailed logs.

**Example:**
```json
{
  "debug": {
    "trace_level": 0
  }
}
```

---

## Configuration File Management

### File Location

**Path:** `/etc/streambox-tv/config.json`
**Managed by:** tvservice (aml_tvserver_streambox)

### Configuration Reload

The configuration file is automatically reloaded when:
1. File is modified (inotify watch)
2. SIGHUP signal is sent to tvservice

### Configuration Validation

tvservice validates configuration values on load:
- Game mode: 0-2
- VRR mode: 0-2
- HDMI source: "HDMI1"-"HDMI4"
- Latency: 1000-100000 microseconds
- Channels: 1-8
- Trace level: 0-3

Invalid values are automatically corrected to defaults.

---

## Configuration Examples

### Gaming Profile

Optimized for low-latency gaming:

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
    "latency_us": 10000,
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

### High Quality Audio

Optimized for high-quality audio:

```json
{
  "video": {
    "game_mode": 0,
    "vrr_mode": 2,
    "hdmi_source": "HDMI2"
  },
  "audio": {
    "enabled": true,
    "capture_device": "hw:0,2",
    "playback_device": "hw:0,0",
    "latency_us": 20000,
    "sample_format": "S32_LE",
    "channels": 8,
    "sample_rate": 96000
  },
  "hdcp": {
    "enabled": true,
    "version": "auto"
  },
  "debug": {
    "trace_level": 0
  }
}
```

### Debug Mode

Enabled for debugging:

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
    "trace_level": 3
  }
}
```

---

## Integration with cockpit-streambox-settings

The cockpit-streambox-settings plugin provides a UI for managing these settings:

### Read Configuration

```python
import json

with open("/etc/streambox-tv/config.json", "r") as f:
    config = json.load(f)
```

### Write Configuration

```python
import json

config = {
    "video": {
        "game_mode": 2,
        "vrr_mode": 2,
        "hdmi_source": "HDMI2"
    },
    # ... other sections
}

with open("/etc/streambox-tv/config.json", "w") as f:
    json.dump(config, f, indent=2)
```

### Reload Configuration

```python
import os
import signal

# Send SIGHUP to tvservice to reload config
os.kill(os.getpid("tvservice"), signal.SIGHUP)
```

---

## Related Documents

- [Overview](./overview.md) - Architecture overview
- [API Specification](./api.md) - D-Bus API for tvserver settings
- [Guidelines](./guidelines.md) - Development guidelines
- [Operations](./operations.md) - Debugging and diagnostics
