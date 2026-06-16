# Proxmox LXC Ubuntu 24.04 Deployment Guide

This guide details how to push the HRMS project from your local Mac to a GitHub repository, configure an Ubuntu 24.04 Linux Container (LXC) on Proxmox, and deploy the entire stack directly on the server without Docker (utilizing MySQL 8, Redis, Gunicorn, Celery, Nginx, and systemd).

---

## Phase 1: Pushing Code from Local Mac to GitHub

Open the terminal on your local Mac and run the following commands inside the `/Users/mivu2k/Desktop/hr` directory:

1.  **Initialize Git Repository**:
    ```bash
    git init
    ```
2.  **Add Files to Commit (respecting the `.gitignore` setup)**:
    ```bash
    git add .
    ```
3.  **Perform Initial Commit**:
    ```bash
    git commit -m "Initial commit: HRMS with ZKTeco simulator support"
    ```
4.  **Rename branch to main**:
    ```bash
    git branch -M main
    ```
5.  **Add your GitHub repository remote url**:
    ```bash
    # Replace <username> and <repository> with your actual GitHub path
    git remote add origin https://github.com/<username>/<repository>.git
    ```
6.  **Push code to GitHub**:
    ```bash
    git push -u origin main
    ```

---

## Phase 2: Proxmox LXC Ubuntu 24.04 Container Creation

1.  Log in to your **Proxmox Virtual Environment** web GUI.
2.  Click **Create CT** (top right corner).
3.  **General Tab**:
    *   Set Hostname (e.g., `hrms-portal`).
    *   Enter Password for `root`.
4.  **Template Tab**:
    *   Select your storage containing templates and choose `ubuntu-24.04-standard` LXC template.
5.  **Root Disk Tab**:
    *   Set storage and size (8GB - 20GB is sufficient).
6.  **CPU Tab**:
    *   Set cores (2 cores recommended).
7.  **Memory Tab**:
    *   Set RAM (e.g., 2048 MB RAM + 512 MB Swap).
8.  **Network Tab**:
    *   Bridge: `vmbr0`.
    *   IPv4: Set `Static` and enter an IP address (e.g., `192.168.1.150/24`) and gateway (e.g., `192.168.1.1`).
9.  **Confirm** and check the box to start the container after creation.

---

## Phase 3: Server Package Installation

SSH into your Proxmox LXC container (e.g., `ssh root@192.168.1.150`) and perform package setups:

1.  **Update Package Lists**:
    ```bash
    apt update && apt upgrade -y
    ```
2.  **Add NodeSource Repository for Node 20**:
    ```bash
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    ```
3.  **Install Essential Packages & Node.js**:
    ```bash
    apt install -y git python3 python3-pip python3-venv python3-dev build-essential libmysqlclient-dev pkg-config redis-server nginx nodejs
    ```
4.  **Configure MySQL 8 Database**:
    *   Install MySQL Server:
        ```bash
        apt install -y mysql-server
        ```
    *   Start and enable MySQL:
        ```bash
        systemctl start mysql
        systemctl enable mysql
        ```
    *   Log in to MySQL command line:
        ```bash
        mysql -u root
        ```
    *   Run SQL commands inside prompt to initialize database:
        ```sql
        CREATE DATABASE hrms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        CREATE USER 'hrms_user'@'localhost' IDENTIFIED BY 'hrms_password';
        GRANT ALL PRIVILEGES ON hrms_db.* TO 'hrms_user'@'localhost';
        FLUSH PRIVILEGES;
        EXIT;
        ```

---

## Phase 4: Application Code Checkout & Setup

1.  **Clone the Repository**:
    ```bash
    cd /var/www
    git clone https://github.com/<username>/<repository>.git hrms
    cd hrms
    ```
2.  **Create Python Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install --upgrade pip
    pip install -r backend/requirements.txt
    ```
4.  **Configure Environment Variables**:
    We will configure environment variables directly inside the systemd services (next phase).
5.  **Compile Vue 3 Frontend static files**:
    ```bash
    cd frontend
    npm install
    npm run build
    cd ..
    ```
    *This generates built files inside `/var/www/hrms/frontend/dist/` ready to be served by Nginx.*

---

## Phase 5: Production Service Configurations (Systemd)

We will configure three background services: Gunicorn (Web API), Celery Worker (Biometric logs download), and Celery Beat (Periodic sync timers).

### 1. Configure Gunicorn Service
Create service file `/etc/systemd/system/hrms-backend.service`:
```ini
[Unit]
Description=Gunicorn daemon for Django HRMS Backend
After=network.target mysql.service redis-server.service

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/hrms/backend
Environment="HRMS_DB_ENGINE=mysql"
Environment="HRMS_DB_NAME=hrms_db"
Environment="HRMS_DB_USER=hrms_user"
Environment="HRMS_DB_PASSWORD=hrms_password"
Environment="HRMS_DB_HOST=localhost"
Environment="HRMS_DB_PORT=3306"
Environment="CELERY_BROKER_URL=redis://localhost:6379/0"
Environment="CELERY_RESULT_BACKEND=redis://localhost:6379/0"
Environment="DJANGO_DEBUG=False"
Environment="DJANGO_SECRET_KEY=production-secret-key-change-me"
ExecStart=/var/www/hrms/venv/bin/gunicorn hrms.wsgi:application --bind 127.0.0.1:8000 --workers 3

[Install]
WantedBy=multi-user.target
```

### 2. Configure Celery Worker Service
Create service file `/etc/systemd/system/hrms-worker.service`:
```ini
[Unit]
Description=Celery Worker for HRMS Biometric Logs Sync
After=network.target hrms-backend.service

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/hrms/backend
Environment="HRMS_DB_ENGINE=mysql"
Environment="HRMS_DB_NAME=hrms_db"
Environment="HRMS_DB_USER=hrms_user"
Environment="HRMS_DB_PASSWORD=hrms_password"
Environment="HRMS_DB_HOST=localhost"
Environment="HRMS_DB_PORT=3306"
Environment="CELERY_BROKER_URL=redis://localhost:6379/0"
Environment="CELERY_RESULT_BACKEND=redis://localhost:6379/0"
ExecStart=/var/www/hrms/venv/bin/celery -A hrms worker --loglevel=info

[Install]
WantedBy=multi-user.target
```

### 3. Configure Celery Beat Service
Create service file `/etc/systemd/system/hrms-beat.service`:
```ini
[Unit]
Description=Celery Beat Scheduler for HRMS Biometric Logs Sync
After=network.target hrms-backend.service

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/hrms/backend
Environment="HRMS_DB_ENGINE=mysql"
Environment="HRMS_DB_NAME=hrms_db"
Environment="HRMS_DB_USER=hrms_user"
Environment="HRMS_DB_PASSWORD=hrms_password"
Environment="HRMS_DB_HOST=localhost"
Environment="HRMS_DB_PORT=3306"
Environment="CELERY_BROKER_URL=redis://localhost:6379/0"
Environment="CELERY_RESULT_BACKEND=redis://localhost:6379/0"
ExecStart=/var/www/hrms/venv/bin/celery -A hrms beat --loglevel=info

[Install]
WantedBy=multi-user.target
```

---

## Phase 6: Nginx Reverse Proxy Configuration

Nginx will serve the compiled Vue 3 files directly, handle `/media/` asset uploads, and proxy the `/api/` and `/admin/` requests to Gunicorn.

Create Nginx site configuration `/etc/nginx/sites-available/hrms`:
```nginx
server {
    listen 80;
    server_name 192.168.1.150; # Replace with your Proxmox container IP or domain

    # Frontend Vue 3 Static build
    location / {
        root /var/www/hrms/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Django Admin Panel
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Ninja APIs
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Media uploads (profile pictures, CNIC documents)
    location /media/ {
        alias /var/www/hrms/backend/media/;
    }

    # Staticfiles (Django admin stylesheet assets)
    location /static/ {
        alias /var/www/hrms/backend/staticfiles/;
    }

    # Logs
    access_log /var/log/nginx/hrms_access.log;
    error_log /var/log/nginx/hrms_error.log;
}
```

Enable site configuration:
```bash
ln -s /etc/nginx/sites-available/hrms /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

---

## Phase 7: Application Initialization & Launch

Execute the following commands on the container to initialize database structures and boot services:

1.  **Database Migration & Seeding**:
    ```bash
    cd /var/www/hrms/backend
    # Activate venv
    source ../venv/bin/activate
    
    # Run migrations against MySQL
    export HRMS_DB_ENGINE=mysql
    export HRMS_DB_NAME=hrms_db
    export HRMS_DB_USER=hrms_user
    export HRMS_DB_PASSWORD=hrms_password
    export HRMS_DB_HOST=localhost
    export HRMS_DB_PORT=3306
    
    python manage.py collectstatic --noinput
    python manage.py migrate
    python seed.py
    ```
2.  **Start and Enable Services**:
    ```bash
    systemctl daemon-reload
    
    # Enable Gunicorn and Workers to launch on reboot
    systemctl enable hrms-backend hrms-worker hrms-beat
    
    # Start the services
    systemctl start hrms-backend hrms-worker hrms-beat
    ```
3.  **Verify Statuses**:
    ```bash
    systemctl status hrms-backend
    systemctl status hrms-worker
    systemctl status hrms-beat
    ```

You can now open the IP of the Proxmox container (`http://192.168.1.150`) in any browser to access the fully functional HRMS portal!
