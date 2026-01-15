#!/bin/bash
# Setup systemd services for Discord Receipt Bot
# Run this script on the GCP server

set -e

echo "=== Setting up systemd services for Discord Receipt Bot ==="

# Create production service
echo "📝 Creating production service file..."
sudo tee /etc/systemd/system/discord-bot.service > /dev/null << 'EOF'
[Unit]
Description=Discord Receipt Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=botuser
Group=botuser
WorkingDirectory=/opt/discord-bot/app

# Environment
Environment="PATH=/home/botuser/.conda/envs/discord_env/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/discord-bot/app/.env.production

# Execution
ExecStart=/home/botuser/.conda/envs/discord_env/bin/python -m bot.main
ExecReload=/bin/kill -HUP $MAINPID

# Restart policy
Restart=always
RestartSec=10s

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=discord-bot

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/discord-bot/app/data /var/log/discord-bot

# Resource limits
LimitNOFILE=4096
MemoryMax=1G

[Install]
WantedBy=multi-user.target
EOF

# Create development service
echo "📝 Creating development service file..."
sudo tee /etc/systemd/system/discord-bot-dev.service > /dev/null << 'EOF'
[Unit]
Description=Discord Receipt Bot (Development)
After=network.target

[Service]
Type=simple
User=botuser
Group=botuser
WorkingDirectory=/opt/discord-bot/app

Environment="PATH=/home/botuser/.conda/envs/discord_env/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/discord-bot/app/.env.development

ExecStart=/home/botuser/.conda/envs/discord_env/bin/python -m bot.main

Restart=always
RestartSec=10s

StandardOutput=journal
StandardError=journal
SyslogIdentifier=discord-bot-dev

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ReadWritePaths=/opt/discord-bot/app/data

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable services
echo "✅ Enabling services..."
sudo systemctl enable discord-bot.service
sudo systemctl enable discord-bot-dev.service

echo ""
echo "=== Systemd services created and enabled! ==="
echo ""
echo "To start the services, run:"
echo "  sudo systemctl start discord-bot.service"
echo "  sudo systemctl start discord-bot-dev.service"
echo ""
echo "To check status:"
echo "  sudo systemctl status discord-bot.service"
echo "  sudo systemctl status discord-bot-dev.service"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u discord-bot.service -f"
echo "  sudo journalctl -u discord-bot-dev.service -f"
