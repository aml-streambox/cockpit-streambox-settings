# cockpit-streambox-settings - Operations Guide

This document provides guidance for debugging, monitoring, and operating the cockpit-streambox-settings system.

---

## System Services

### streambox-settings Daemon

The main daemon that provides D-Bus interface and manages system settings.

**Service Name:** `streambox-settings`
**Systemd Unit:** `streambox-settings.service`

**Service Management:**
```bash
# Start service
systemctl start streambox-settings

# Stop service
systemctl stop streambox-settings

# Restart service
systemctl restart streambox-settings

# Check status
systemctl status streambox-settings

# Enable at boot
systemctl enable streambox-settings

# Disable at boot
systemctl disable streambox-settings
```

### tvservice

The hardware service that manages HDMI RX/TX and configuration.

**Service Name:** `tvservice`
**Systemd Unit:** `tvservice.service`

**Service Management:**
```bash
# Check status
systemctl status tvservice

# Restart if needed
systemctl restart tvservice
```

### Network Services

**NetworkManager:** Manages wired and WiFi connections
```bash
# Check status
systemctl status NetworkManager

# Restart if needed
systemctl restart NetworkManager
```

**hostapd:** WiFi Access Point daemon
```bash
# Check status
systemctl status hostapd

# Restart if needed
systemctl restart hostapd
```

---

## Logging

### Log Locations

**streambox-settings Logs:**
- **Journal:** `journalctl -u streambox-settings`
- **Log File:** `/var/log/streambox-settings/daemon.log` (if configured)

**tvservice Logs:**
- **Journal:** `journalctl -u tvservice`
- **Log File:** `/var/log/tvservice/tvservice.log`

**Network Logs:**
- **NetworkManager:** `journalctl -u NetworkManager`
- **hostapd:** `journalctl -u hostapd`
- **wpa_supplicant:** `journalctl -u wpa_supplicant`

**System Logs:**
- **Kernel:** `dmesg` or `journalctl -k`
- **System:** `journalctl`

### Viewing Logs

**Real-time monitoring:**
```bash
# Monitor streambox-settings
journalctl -u streambox-settings -f

# Monitor tvservice
journalctl -u tvservice -f

# Monitor NetworkManager
journalctl -u NetworkManager -f

# Monitor all services
journalctl -u streambox-settings -u tvservice -u NetworkManager -f
```

**Filtering logs:**
```bash
# Show errors only
journalctl -u streambox-settings -p err

# Show last 100 lines
journalctl -u streambox-settings -n 100

# Show logs from last hour
journalctl -u streambox-settings --since "1 hour ago"
```

**Exporting logs:**
```bash
# Export to file
journalctl -u streambox-settings > streambox-settings.log

# Export with context
journalctl -u streambox-settings -b > streambox-settings-boot.log
```

### Log Levels

| Level | Description |
|--------|-------------|
| DEBUG | Detailed debugging information |
| INFO | General informational messages |
| WARNING | Warning messages |
| ERROR | Error messages |
| CRITICAL | Critical errors |

**Setting log level:**
```bash
# Set debug mode
export STREAMBOX_SETTINGS_DEBUG=1
systemctl restart streambox-settings

# Or via systemd override
systemctl edit streambox-settings
# Add: Environment="STREAMBOX_SETTINGS_DEBUG=1"
```

---

## Diagnostics

### System Status Check

**Check all services:**
```bash
# Check streambox-settings
systemctl status streambox-settings

# Check tvservice
systemctl status tvservice

# Check NetworkManager
systemctl status NetworkManager

# Check hostapd
systemctl status hostapd

# Check Cockpit
systemctl status cockpit
```

**Check hardware interfaces:**
```bash
# Check network interfaces
ip link show

# Check WiFi interfaces
iwconfig

# Check storage devices
lsblk

# Check ALSA devices
aplay -l
arecord -l
```

### Hardware Information

**Get system information:**
```bash
# System hostname
hostname

# System time and date
date

# System timezone
timedatectl

# System locale
locale

# System uptime
uptime

# System load
cat /proc/loadavg

# Memory usage
free -h

# Disk usage
df -h
```

**Get network information:**
```bash
# Network interfaces
nmcli device status

# WiFi networks
nmcli device wifi list

# WiFi AP status
iwconfig

# IP addresses
ip addr show

# Routing table
ip route show

# DNS configuration
cat /etc/resolv.conf
```

**Get storage information:**
```bash
# Block devices
lsblk

# Mounted filesystems
findmnt

# Disk usage
df -h

# SDCard information
cat /sys/block/mmcblk0/size
cat /sys/block/mmcblk0/device/type
```

### D-Bus Interface Testing

**List D-Bus services:**
```bash
# Check if service is registered
busctl --system list | grep streambox

# Check service details
busctl --system introspect org.cockpit.StreamboxSettings /org/cockpit/StreamboxSettings
```

**Test D-Bus methods:**
```bash
# Get basic settings
busctl --system call org.cockpit.StreamboxSettings \
  /org/cockpit/StreamboxSettings \
  org.cockpit.StreamboxSettings1 \
  GetBasicSettings

# Get network status
busctl --system call org.cockpit.StreamboxSettings \
  /org/cockpit/StreamboxSettings \
  org.cockpit.StreamboxSettings1 \
  GetNetworkStatus

# Get tvserver config
busctl --system call org.cockpit.StreamboxSettings \
  /org/cockpit/StreamboxSettings \
  org.cockpit.StreamboxSettings1 \
  GetTvserverConfig

# Get storage devices
busctl --system call org.cockpit.StreamboxSettings \
  /org/cockpit/StreamboxSettings \
  org.cockpit.StreamboxSettings1 \
  GetStorageDevices
```

### Network Connectivity

**Check Cockpit access:**
```bash
# Check if Cockpit is listening
netstat -tlnp | grep cockpit

# Test Cockpit web interface
curl -k https://localhost:9090
```

**Check network connectivity:**
```bash
# Test DNS resolution
nslookup google.com

# Test network connectivity
ping -c 4 8.8.8.8

# Test HTTP connectivity
curl -I https://www.google.com
```

---

## Common Issues and Solutions

### Service Won't Start

**Symptoms:**
- Service fails to start
- Service crashes immediately

**Troubleshooting:**
```bash
# Check service status
systemctl status streambox-settings

# Check logs for errors
journalctl -u streambox-settings -n 50

# Check dependencies
systemctl list-dependencies streambox-settings

# Check if tvservice is running
systemctl status tvservice
```

**Common Causes:**
1. tvservice not running
2. D-Bus not available
3. Missing dependencies
4. Configuration file errors

**Solutions:**
1. Start tvservice: `systemctl start tvservice`
2. Restart D-Bus: `systemctl restart dbus`
3. Install missing dependencies
4. Check configuration file syntax

### Hostname Not Changing

**Symptoms:**
- Hostname change fails
- Hostname reverts after reboot

**Troubleshooting:**
```bash
# Check current hostname
hostname

# Check hostnamectl
hostnamectl status

# Check /etc/hostname
cat /etc/hostname

# Check logs
journalctl -u streambox-settings | grep hostname
```

**Common Causes:**
1. Invalid hostname format
2. Permission denied
3. NetworkManager conflict

**Solutions:**
1. Use valid hostname format (alphanumeric, hyphens, dots)
2. Run as root
3. Check NetworkManager hostname settings

### Timezone Not Applying

**Symptoms:**
- Timezone change fails
- System time incorrect

**Troubleshooting:**
```bash
# Check current timezone
timedatectl

# Check available timezones
timedatectl list-timezones

# Check /etc/localtime
ls -l /etc/localtime

# Check logs
journalctl -u streambox-settings | grep timezone
```

**Common Causes:**
1. Invalid timezone name
2. Timezone database not installed
3. NTP not configured

**Solutions:**
1. Use valid timezone from `timedatectl list-timezones`
2. Install tzdata package
3. Configure NTP server

### Network Not Connecting

**Symptoms:**
- Wired network not connecting
- WiFi client not connecting
- WiFi AP not starting

**Troubleshooting:**
```bash
# Check NetworkManager status
systemctl status NetworkManager

# Check network interfaces
nmcli device status

# Check WiFi status
nmcli device wifi status

# Check hostapd status
systemctl status hostapd

# Check logs
journalctl -u NetworkManager -n 50
journalctl -u hostapd -n 50
```

**Common Causes:**
1. Network cable not connected
2. WiFi driver not loaded
3. Invalid network configuration
4. DHCP server not responding
5. WiFi password incorrect

**Solutions:**
1. Check physical cable connection
2. Load WiFi driver: `modprobe <driver>`
3. Verify network configuration
4. Check DHCP server availability
5. Verify WiFi password

### WiFi AP Not Working

**Symptoms:**
- WiFi AP not starting
- Cannot connect to WiFi AP
- DHCP not assigning IPs

**Troubleshooting:**
```bash
# Check hostapd status
systemctl status hostapd

# Check hostapd configuration
cat /etc/hostapd/hostapd.conf

# Check dnsmasq status
systemctl status dnsmasq

# Check WiFi interface
iwconfig

# Check logs
journalctl -u hostapd -n 50
journalctl -u dnsmasq -n 50
```

**Common Causes:**
1. WiFi driver doesn't support AP mode
2. Invalid hostapd configuration
3. dnsmasq not running
4. IP address conflict
5. Channel interference

**Solutions:**
1. Check WiFi driver AP mode support
2. Verify hostapd configuration
3. Start dnsmasq: `systemctl start dnsmasq`
4. Use different IP range
5. Change WiFi channel

### TVServer Configuration Not Applying

**Symptoms:**
- Configuration changes not taking effect
- tvservice not reloading config

**Troubleshooting:**
```bash
# Check tvservice status
systemctl status tvservice

# Check config file
cat /etc/streambox-tv/config.json

# Check config file permissions
ls -l /etc/streambox-tv/config.json

# Check logs
journalctl -u tvservice | grep config

# Manually trigger reload
killall -HUP tvservice
```

**Common Causes:**
1. Invalid JSON syntax
2. Invalid configuration values
3. Permission denied
4. tvservice not watching file

**Solutions:**
1. Validate JSON syntax
2. Use valid configuration values
3. Fix file permissions: `chmod 644 /etc/streambox-tv/config.json`
4. Restart tvservice: `systemctl restart tvservice`

### Storage Not Mounting

**Symptoms:**
- SDCard not detected
- Cannot mount storage device
- Mount point not accessible

**Troubleshooting:**
```bash
# Check block devices
lsblk

# Check device details
blkid /dev/mmcblk0

# Check mount points
findmnt

# Check filesystem type
file -s /dev/mmcblk0

# Check logs
journalctl -u streambox-settings | grep storage
dmesg | grep mmcblk
```

**Common Causes:**
1. Device not inserted
2. Filesystem not supported
3. Corrupted filesystem
4. Mount point already in use
5. Permission denied

**Solutions:**
1. Insert storage device
2. Format with supported filesystem
3. Repair filesystem: `fsck /dev/mmcblk0`
4. Unmount existing mount: `umount /mnt/sdcard`
5. Run as root

### Storage Format Fails

**Symptoms:**
- Format operation fails
- Format takes too long
- Device becomes unusable

**Troubleshooting:**
```bash
# Check device status
lsblk

# Check if device is mounted
findmnt

# Check device size
blockdev --getsize64 /dev/mmcblk0

# Check logs
journalctl -u streambox-settings | grep format
dmesg | grep mmcblk
```

**Common Causes:**
1. Device is mounted
2. Device is write-protected
3. Insufficient space
4. Unsupported filesystem type
5. Device failure

**Solutions:**
1. Unmount device first: `umount /dev/mmcblk0`
2. Remove write protection
3. Use smaller filesystem or delete files
4. Use supported filesystem (ext4, vfat)
5. Replace device if failed

### Cockpit UI Not Accessible

**Symptoms:**
- Cannot access Cockpit web interface
- Connection timeout
- Blank page

**Troubleshooting:**
```bash
# Check Cockpit service
systemctl status cockpit

# Check network connectivity
ping <device-ip>

# Check firewall
iptables -L | grep cockpit

# Check Cockpit listening ports
netstat -tlnp | grep cockpit

# Check streambox-settings service
systemctl status streambox-settings
```

**Common Causes:**
1. Cockpit service not running
2. Network connectivity issue
3. Firewall blocking
4. Port conflict
5. streambox-settings not running

**Solutions:**
1. Start Cockpit: `systemctl start cockpit`
2. Check network configuration
3. Configure firewall to allow port 9090
4. Check for port conflicts
5. Start streambox-settings: `systemctl start streambox-settings`

---

## Performance Monitoring

### CPU Usage

**Monitor CPU usage:**
```bash
# Real-time monitoring
top -p $(pgrep streambox-settings)

# Check average usage
mpstat -P ALL 1

# Check process usage
ps aux | grep streambox-settings
```

**Expected CPU Usage:**
- Idle: < 5%
- Active: 10-20%
- High load: > 30% (investigate)

### Memory Usage

**Monitor memory usage:**
```bash
# Check process memory
ps aux | grep streambox-settings

# Check system memory
free -h

# Check memory details
cat /proc/$(pgrep streambox-settings)/status | grep -i mem
```

**Expected Memory Usage:**
- streambox-settings: < 50MB
- tvservice: 100-200MB

### Disk Usage

**Monitor disk usage:**
```bash
# Check log file sizes
du -sh /var/log/streambox-settings/

# Check configuration sizes
du -sh /var/lib/streambox-settings/

# Check overall disk usage
df -h
```

---

## Configuration Backup and Restore

### Backup Configuration

**Export current configuration:**
```bash
# Via Cockpit UI
# Navigate to Settings > Configuration > Export

# Via D-Bus
busctl --system call org.cockpit.StreamboxSettings \
  /org/cockpit/StreamboxSettings \
  org.cockpit.StreamboxSettings1 \
  ExportConfig s "backup-profile"
```

**Backup configuration files:**
```bash
# Backup system configuration
tar -czf streambox-settings-backup.tar.gz /var/lib/streambox-settings/

# Backup tvserver configuration
tar -czf tvserver-config-backup.tar.gz /etc/streambox-tv/

# Backup profiles
tar -czf streambox-profiles-backup.tar.gz /var/lib/streambox-settings/profiles/
```

### Restore Configuration

**Import configuration:**
```bash
# Via Cockpit UI
# Navigate to Settings > Configuration > Import

# Via D-Bus
busctl --system call org.cockpit.StreamboxSettings \
  /org/cockpit/StreamboxSettings \
  org.cockpit.StreamboxSettings1 \
  ImportConfig ss "$(cat backup-profile.json)" true
```

**Restore from backup:**
```bash
# Restore system configuration
tar -xzf streambox-settings-backup.tar.gz -C /

# Restore tvserver configuration
tar -xzf tvserver-config-backup.tar.gz -C /

# Restart services
systemctl restart streambox-settings
systemctl restart tvservice
```

---

## Debug Mode

### Enable Debug Logging

**Enable debug mode:**
```bash
# Set environment variable
export STREAMBOX_SETTINGS_DEBUG=1

# Restart service
systemctl restart streambox-settings

# Or via systemd override
systemctl edit streambox-settings
# Add: Environment="STREAMBOX_SETTINGS_DEBUG=1"
```

### Enable Verbose Hardware Logging

**Enable tvservice debug:**
```bash
# Set debug trace level
# Via Cockpit UI: TVServer Settings > Debug > Trace Level
# Or edit config: /etc/streambox-tv/config.json
# Set: "debug": {"trace_level": 3}

# Restart tvservice
systemctl restart tvservice
```

### Debug Network

**Enable NetworkManager debug:**
```bash
# Set log level
nmcli general logging level DEBUG

# Restart NetworkManager
systemctl restart NetworkManager
```

**Enable hostapd debug:**
```bash
# Set debug level in config
# Edit /etc/hostapd/hostapd.conf
# Add: logger_syslog_level=2

# Restart hostapd
systemctl restart hostapd
```

### Debug D-Bus Communication

**Monitor D-Bus traffic:**
```bash
# Monitor all D-Bus messages
busctl --system monitor

# Monitor specific service
busctl --system monitor org.cockpit.StreamboxSettings
```

---

## System Reset

### Factory Reset

**Reset to default configuration:**
```bash
# Stop service
systemctl stop streambox-settings

# Remove configuration
rm -rf /var/lib/streambox-settings/*

# Restart service
systemctl start streambox-settings
```

**Reset tvserver configuration:**
```bash
# Stop tvservice
systemctl stop tvservice

# Restore default config
cp /etc/streambox-tv/config.json.default /etc/streambox-tv/config.json

# Restart tvservice
systemctl start tvservice
```

### Network Reset

**Reset network configuration:**
```bash
# Reset NetworkManager connections
nmcli connection down <connection-name>
nmcli connection delete <connection-name>

# Restart NetworkManager
systemctl restart NetworkManager
```

**Reset WiFi AP:**
```bash
# Stop hostapd
systemctl stop hostapd

# Reset configuration
# Edit /etc/hostapd/hostapd.conf to defaults

# Restart hostapd
systemctl start hostapd
```

---

## Support and Reporting Issues

### Collect Diagnostic Information

**Generate diagnostic report:**
```bash
# Create diagnostic script
cat > /tmp/diagnose.sh << 'EOF'
#!/bin/bash
echo "=== System Information ==="
uname -a
echo ""

echo "=== Service Status ==="
systemctl status streambox-settings
systemctl status tvservice
systemctl status NetworkManager
systemctl status hostapd
echo ""

echo "=== Recent Logs ==="
journalctl -u streambox-settings -n 50
journalctl -u tvservice -n 50
journalctl -u NetworkManager -n 50
echo ""

echo "=== Hardware Status ==="
lsblk
ip link show
aplay -l
echo ""

echo "=== D-Bus Status ==="
busctl --system list | grep streambox
echo ""

echo "=== Network Status ==="
nmcli device status
nmcli connection show
echo ""

echo "=== Configuration ==="
cat /var/lib/streambox-settings/config.json
cat /etc/streambox-tv/config.json
EOF

chmod +x /tmp/diagnose.sh
/tmp/diagnose.sh > /tmp/diagnostic-report.txt
```

### Reporting Issues

When reporting issues, include:
1. Diagnostic report
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Hardware configuration
6. Software version

---

## References

- [Overview](./overview.md) - Architecture overview
- [API Specification](./api.md) - D-Bus API details
- [TVServer Config Reference](./hardware_reference.md) - tvserver configuration
- [Guidelines](./guidelines.md) - Development guidelines
