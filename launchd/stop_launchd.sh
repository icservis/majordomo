#!/bin/bash

# Stop (unload) the launchd service
# This script unloads the LaunchAgent for the current user

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.majordomo.service.plist"

# Unload the service
echo "Unloading launchd service..."
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || echo "Service was not loaded or already stopped."

# Optionally remove the plist file
read -p "Remove plist file from LaunchAgents? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
    echo "Plist file removed."
else
    echo "Plist file kept in LaunchAgents directory."
fi

echo "Service stopped."

