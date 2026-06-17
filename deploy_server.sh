#!/bin/bash
# Server-side Deployment Script for HRMS Proxmox Container
# This script pulls latest changes, compiles the frontend, runs database migrations, and restarts systemd services.

set -e

# Change directory to project root
cd /var/www/hrms

echo "=== 1. Pulling Latest Changes from GitHub ==="
git pull origin main

echo "=== 2. Compiling Vue 3 Frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== 3. Running Database Migrations ==="
# Extract database configuration directly from hrms-backend systemd service
echo "Reading database configurations..."
export HRMS_DB_ENGINE=$(grep -oP 'Environment="HRMS_DB_ENGINE=\K[^"]+' /etc/systemd/system/hrms-backend.service || echo "mysql")
export HRMS_DB_NAME=$(grep -oP 'Environment="HRMS_DB_NAME=\K[^"]+' /etc/systemd/system/hrms-backend.service || echo "hrms_db")
export HRMS_DB_USER=$(grep -oP 'Environment="HRMS_DB_USER=\K[^"]+' /etc/systemd/system/hrms-backend.service || echo "hrms_user")
export HRMS_DB_PASSWORD=$(grep -oP 'Environment="HRMS_DB_PASSWORD=\K[^"]+' /etc/systemd/system/hrms-backend.service || echo "")
export HRMS_DB_HOST=$(grep -oP 'Environment="HRMS_DB_HOST=\K[^"]+' /etc/systemd/system/hrms-backend.service || echo "localhost")
export HRMS_DB_PORT=$(grep -oP 'Environment="HRMS_DB_PORT=\K[^"]+' /etc/systemd/system/hrms-backend.service || echo "3306")

# Activate virtualenv and run migrate
source venv/bin/activate
cd backend
python manage.py migrate
cd ..

echo "=== 4. Restarting systemd Services & Nginx ==="
systemctl daemon-reload
systemctl restart hrms-backend hrms-worker hrms-beat
systemctl restart nginx

echo "========================================="
echo "=== Deployment Completed Successfully! ==="
echo "========================================="
