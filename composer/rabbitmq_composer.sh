#!/bin/bash
set -euo pipefail

echo " Starting RabbitMQ Service"

sudo -n systemctl start rabbitmq-server 2>/dev/null || true
sudo -n systemctl enable rabbitmq-server >/dev/null 2>&1 || true

sleep 3

echo ""
echo "RabbitMQ status:"
if systemctl is-active --quiet rabbitmq-server; then
  echo "active"
else
  echo "RabbitMQ is NOT active"
  exit 1
fi

echo ""
echo "Listening ports (5672 = AMQP, 15672 = UI):"
ss -lntp | grep -E ':(5672|15672)\b' || true

echo ""
echo "Tailscale IP:"
tailscale ip -4 | head -n1 || true

echo ""
echo "RabbitMQ Management UI:"
echo "http://$(tailscale ip -4 | head -n1):15672"

echo ""
echo "Login:"
echo "Username: appuser"
echo "Password: apppass"

echo " RabbitMQ startup complete"
