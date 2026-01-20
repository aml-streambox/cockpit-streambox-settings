#!/bin/bash

SERVICE_NAME="org.cockpit.StreamboxSettings"
OBJECT_PATH="/org/cockpit/StreamboxSettings"

echo "Checking D-Bus service: $SERVICE_NAME"

if command -v busctl >/dev/null 2>&1; then
    if busctl status --system 2>/dev/null; then
        if busctl --system status "$SERVICE_NAME" 2>/dev/null | grep -q "$OBJECT_PATH"; then
            echo "Service is running and registered on D-Bus"
            exit 0
        else
            echo "Service name registered but object path not found"
            busctl --system | grep -i streambox
            exit 1
        fi
    else
        echo "System bus not available"
        exit 1
    fi
elif command -v dbus-send >/dev/null 2>&1; then
    if dbus-send --system --dest=org.freedesktop.DBus --print-reply --type=method_call /org/freedesktop/DBus org.freedesktop.DBus.GetNameOwner string:"$SERVICE_NAME" 2>/dev/null | grep -q "string"; then
        echo "Service is registered on D-Bus"
        exit 0
    else
        echo "Service not registered on D-Bus"
        exit 1
    fi
else
    echo "Neither busctl nor dbus-send available"
    exit 1
fi
