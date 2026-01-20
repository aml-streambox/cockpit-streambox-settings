#!/bin/bash

set -e

INSTALL_DIR="/usr/lib/streambox-settings"
COCKPIT_DIR="/usr/share/cockpit/streambox-settings"
SYSTEMD_DIR="/etc/systemd/system"
SERVICE_NAME="streambox-settings.service"

echo "==================================="
echo "Streambox Settings Uninstaller"
echo "==================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

echo "Stopping and disabling service..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
systemctl disable "$SERVICE_NAME" 2>/dev/null || true

echo "Removing systemd service..."
rm -f "$SYSTEMD_DIR/$SERVICE_NAME"

echo "Removing D-Bus configuration..."
rm -f "/etc/dbus-1/system.d/org.cockpit.StreamboxSettings.conf"

systemctl daemon-reload

echo "Removing backend files..."
rm -rf "$INSTALL_DIR"

echo "Removing frontend files..."
rm -rf "$COCKPIT_DIR"

echo "Removing configuration directories..."
rm -rf "/var/lib/streambox-settings"

echo "==================================="
echo "Uninstallation complete!"
echo "==================================="
echo ""
