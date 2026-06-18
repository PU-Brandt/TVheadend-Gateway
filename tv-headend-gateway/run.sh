#!/usr/bin/with-contenv sh
set -eu

echo "Starting TV-Headend Gateway add-on UI"
exec python3 /addon_server.py

