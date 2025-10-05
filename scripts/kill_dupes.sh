#!/usr/bin/env bash
set -e
pkill -f "app.py|getUpdates|python-telegram-bot" 2>/dev/null || true
sleep 1
ps aux | grep -E "app\.py|getUpdates|python-telegram-bot" | grep -v grep || true
echo "✅ Дубликаты остановлены."