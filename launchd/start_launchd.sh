#!/bin/bash

# Start (load) the launchd service
# This script loads the LaunchAgent for the current user

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_FILE="$SCRIPT_DIR/com.majordomo.service.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.majordomo.service.plist"

# Copy plist to LaunchAgents directory
echo "Copying plist to LaunchAgents directory..."
cp "$PLIST_FILE" "$LAUNCH_AGENTS_DIR/$PLIST_NAME"

# Load the service
echo "Loading launchd service..."
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_NAME"

echo "Service started. Check logs at:"
echo "  - /tmp/com.majordomo.service.out"
echo "  - /tmp/com.majordomo.service.err"

