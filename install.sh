#!/bin/bash

set -e

INSTALL_DIR="/usr/lib/streambox-settings"
COCKPIT_DIR="/usr/share/cockpit/streambox-settings"
SYSTEMD_DIR="/etc/systemd/system"
SERVICE_NAME="streambox-settings.service"

echo "==================================="
echo "Streambox Settings Installer"
echo "==================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

echo "[0/7] Checking dependencies..."
MISSING_DEPS=""

if ! python3 -c "import dbus" 2>/dev/null; then
    MISSING_DEPS="$MISSING_DEPS python3-dbus"
fi

if ! python3 -c "from gi.repository import GLib" 2>/dev/null; then
    MISSING_DEPS="$MISSING_DEPS python3-gobject"
fi

if ! python3 -c "import asyncio" 2>/dev/null; then
    MISSING_DEPS="$MISSING_DEPS python3-asyncio"
fi

if [ -n "$MISSING_DEPS" ]; then
    echo "Error: Missing Python dependencies: $MISSING_DEPS"
    echo "Please install them first:"
    echo "  opkg install python3-dbus python3-gobject python3-asyncio"
    exit 1
fi

echo "[1/7] Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$COCKPIT_DIR"
mkdir -p "/var/lib/streambox-settings/profiles"
mkdir -p "/var/log/streambox-settings"

echo "[2/7] Installing backend files..."
cp -v backend/*.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/main.py"

echo "[3/7] Installing frontend files..."
cp -v frontend/*.html "$COCKPIT_DIR/"
cp -v frontend/*.js "$COCKPIT_DIR/"
cp -v frontend/*.css "$COCKPIT_DIR/"
cp -v frontend/manifest.json "$COCKPIT_DIR/"

echo "[4/7] Installing systemd service..."
cp -v yocto/files/streambox-settings.service "$SYSTEMD_DIR/"

echo "[4.5/6] Installing D-Bus configuration..."
DBUS_SYSTEM_DIR="/etc/dbus-1/system.d"
mkdir -p "$DBUS_SYSTEM_DIR"
cp -v yocto/files/org.cockpit.StreamboxSettings.conf "$DBUS_SYSTEM_DIR/"

echo "[5/6] Setting up directories and permissions..."
chmod 755 "$INSTALL_DIR"
chmod 644 "$INSTALL_DIR"/*.py
chmod 755 "$INSTALL_DIR/main.py"

chmod 755 "$COCKPIT_DIR"
chmod 644 "$COCKPIT_DIR"/*

chmod 755 "/var/lib/streambox-settings"
chmod 755 "/var/lib/streambox-settings/profiles"
chmod 755 "/var/log/streambox-settings"

echo "[6/7] Installing D-Bus configuration..."
DBUS_SYSTEM_DIR="/etc/dbus-1/system.d"
if [ -d "$DBUS_SYSTEM_DIR" ]; then
    cp -f "./yocto/files/org.cockpit.StreamboxSettings.conf" "$DBUS_SYSTEM_DIR/"
    chmod 644 "$DBUS_SYSTEM_DIR/org.cockpit.StreamboxSettings.conf"
    echo "D-Bus configuration installed to $DBUS_SYSTEM_DIR"
fi

echo "Reloading systemd and D-Bus..."
systemctl daemon-reload

if [ -x "$(command -v dbus-send)" ]; then
    systemctl reload dbus
fi

echo "Checking D-Bus system availability..."
if command -v busctl >/dev/null 2>&1; then
    busctl --system list | grep -E "NAME|org.freedesktop.DBus" || echo "D-Bus system bus not fully available"
fi

echo "[7/7] Enabling and starting service..."
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo ""
echo "==================================="
echo "Installation complete!"
echo "==================================="
echo ""
echo "Verifying D-Bus service..."
if [ -f "./yocto/files/check-service.sh" ]; then
    chmod +x ./yocto/files/check-service.sh
    ./yocto/files/check-service.sh || true
fi

echo ""
echo "Service status:"
systemctl status "$SERVICE_NAME" --no-pager || true

echo ""
echo "D-Bus status:"
if command -v busctl >/dev/null 2>&1; then
    busctl --system list | grep -q "org.cockpit.StreamboxSettings" && echo "Service registered on D-Bus: org.cockpit.StreamboxSettings" || echo "Service not registered on D-Bus"
fi

echo ""
echo "Running diagnostics..."
if [ -f "./diagnose-dbus.sh" ]; then
    chmod +x ./diagnose-dbus.sh
    echo "Run './diagnose-dbus.sh' for detailed D-Bus diagnostics"
fi

echo ""
echo "Access Streambox Settings at:"
echo "https://$(hostname -I | awk '{print $1}'):9090"
echo ""
