#!/bin/bash
echo "=== Discord Bot Monitoring ==="
echo ""
echo "Service Status:"
systemctl status discord-bot.service --no-pager | head -10
echo ""
echo "Resource Usage:"
ps aux | grep "python -m bot.main" | grep -v grep
echo ""
echo "Disk Usage:"
du -sh /opt/discord-bot/data/*
echo ""
echo "Recent Errors (last 50 lines):"
journalctl -u discord-bot.service --since "1 hour ago" | grep -i error | tail -50
