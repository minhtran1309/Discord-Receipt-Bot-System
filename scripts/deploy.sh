#!/bin/bash
set -e

ENVIRONMENT=${1:-production}
DEPLOY_DIR="/opt/discord-bot"
BACKUP_DIR="/opt/discord-bot/backups"
SOURCE_DIR="/tmp/discord-bot-deploy"

echo "=== Deploying Discord Bot to $ENVIRONMENT environment ==="

# Create backup
echo "Creating backup..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/discord-bot-${TIMESTAMP}.tar.gz \
    -C $DEPLOY_DIR \
    --exclude='data' \
    --exclude='backups' \
    --exclude='__pycache__' \
    . || echo "No existing deployment to backup"

# Stop service
echo "Stopping service..."
if [ "$ENVIRONMENT" = "production" ]; then
    systemctl stop discord-bot.service || true
else
    systemctl stop discord-bot-dev.service || true
fi

# Sync code
echo "Syncing code..."
rsync -av --delete \
    --exclude='data/' \
    --exclude='data-dev/' \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='.env' \
    --exclude='.env.*' \
    --exclude='credentials/' \
    $SOURCE_DIR/ $DEPLOY_DIR/

# Set permissions
echo "Setting permissions..."
chown -R botuser:botuser $DEPLOY_DIR
chmod -R 755 $DEPLOY_DIR
chmod 700 $DEPLOY_DIR/data $DEPLOY_DIR/data-dev 2>/dev/null || true

# Update conda environment
echo "Updating conda environment..."
sudo -u botuser bash << EOF
source /opt/miniconda/etc/profile.d/conda.sh
conda activate discord-bot
conda env update -f $DEPLOY_DIR/environment.yml --prune
pip install -r $DEPLOY_DIR/requirements.txt
EOF

# Set correct environment symlink
if [ "$ENVIRONMENT" = "production" ]; then
    ln -sf $DEPLOY_DIR/.env.production $DEPLOY_DIR/.env
    echo "Environment set to: production"
else
    ln -sf $DEPLOY_DIR/.env.development $DEPLOY_DIR/.env
    echo "Environment set to: development"
fi

# Start service
echo "Starting service..."
if [ "$ENVIRONMENT" = "production" ]; then
    systemctl start discord-bot.service
    systemctl enable discord-bot.service
else
    systemctl start discord-bot-dev.service
    systemctl enable discord-bot-dev.service
fi

# Wait and check status
echo "Waiting for service to start..."
sleep 5

if [ "$ENVIRONMENT" = "production" ]; then
    systemctl status discord-bot.service --no-pager
else
    systemctl status discord-bot-dev.service --no-pager
fi

echo "=== Deployment completed successfully ==="
echo "View logs with: journalctl -u discord-bot${ENVIRONMENT:+-dev}.service -f"
