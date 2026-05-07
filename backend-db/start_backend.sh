#!/usr/bin/env bash
set -e

APP_DIR="$HOME/music/thisismusic/backend"

echo "Starting Backend Service..."
cd "$APP_DIR"

python3 main.py
