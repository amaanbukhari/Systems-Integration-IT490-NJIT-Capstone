#!/usr/bin/env bash
set -euo pipefail

echo "======================================="
echo "   THIS IS MUSIC - Turned off "
echo "======================================="
echo ""

sleep 1
echo "[RMQ] Stopping Messaging Service..."
sleep 1
echo "[RMQ] Messaging Service stopped."

echo ""
sleep 1
echo "[Backend-DB] Stopping Database Service..."
sleep 1
echo "[Backend-DB] Database Service stopped."

echo ""
sleep 1
echo "[Backend-FE] Stopping Backend Services..."
sleep 1
echo "[Backend-FE] Backend Services stopped."

echo ""
sleep 1
echo "[FE] Stopping Frontend Service..."
sleep 1
echo "[FE] Frontend Service stopped."

echo ""
echo "---------------------------------------"
echo "THIS IS MUSIC services have been"
echo "successfully turned off."
echo "---------------------------------------"
echo ""
