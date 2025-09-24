#!/bin/bash

# Solar Inverter Data Collector Installation Script
# This script sets up the complete environment on a Linux system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="solar-inverter-collector"
APP_DIR="/opt/solar-inverter"
SERVICE_USER="solar"
VENV_DIR="$APP_DIR/venv"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

install_dependencies() {
    print_status "Installing system dependencies..."

    # Update package list
    apt-get update

    # Install required packages
    apt-get install -y python3 python3-pip python3-venv cron mysql-client

    print_success "System dependencies installed"
}

create_user() {
    print_status "Creating service user..."

    if id "$SERVICE_USER" &>/dev/null; then
        print_warning "User $SERVICE_USER already exists"
    else
        useradd --system --home-dir "$APP_DIR" --shell /bin/bash "$SERVICE_USER"
        print_success "User $SERVICE_USER created"
    fi
}

setup_application_directory() {
    print_status "Setting up application directory..."

    # Create directory structure
    mkdir -p "$APP_DIR"/{logs,config}

    # Copy application files
    cp -r . "$APP_DIR/"

    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

    # Set permissions
    chmod +x "$APP_DIR/collect_solar_data.py"
    chmod +x "$APP_DIR/setup_database.py"

    print_success "Application directory setup complete"
}

setup_python_environment() {
    print_status "Setting up Python virtual environment..."

    # Create virtual environment as the service user
    sudo -u "$SERVICE_USER" python3 -m venv "$VENV_DIR"

    # Install Python dependencies
    sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install --upgrade pip
    sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

    print_success "Python environment setup complete"
}

setup_systemd_service() {
    print_status "Setting up systemd service..."

    cat > /etc/systemd/system/${APP_NAME}.service << EOF
[Unit]
Description=Solar Inverter Data Collector
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=oneshot
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python collect_solar_data.py
StandardOutput=journal
StandardError=journal
SyslogIdentifier=solar-collector

[Install]
WantedBy=multi-user.target
EOF

    # Setup systemd timer for every minute execution
    cat > /etc/systemd/system/${APP_NAME}.timer << EOF
[Unit]
Description=Run Solar Inverter Data Collector every minute
Requires=${APP_NAME}.service

[Timer]
OnCalendar=*:*:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    systemctl daemon-reload
    systemctl enable ${APP_NAME}.timer

    print_success "Systemd service and timer created"
}

setup_logrotate() {
    print_status "Setting up log rotation..."

    cat > /etc/logrotate.d/solar-inverter << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su $SERVICE_USER $SERVICE_USER
}
EOF

    print_success "Log rotation configured"
}

setup_database_config() {
    print_status "Setting up database configuration..."

    # Run database setup as service user
    print_status "Please configure the database..."
    sudo -u "$SERVICE_USER" "$VENV_DIR/bin/python" "$APP_DIR/setup_database.py"

    print_success "Database configuration complete"
}

start_services() {
    print_status "Starting services..."

    systemctl start ${APP_NAME}.timer
    systemctl status ${APP_NAME}.timer --no-pager -l

    print_success "Services started"
}

show_status() {
    print_status "Installation Summary:"
    echo "  Application Directory: $APP_DIR"
    echo "  Service User: $SERVICE_USER"
    echo "  Virtual Environment: $VENV_DIR"
    echo "  Service Name: ${APP_NAME}.service"
    echo "  Timer Name: ${APP_NAME}.timer"
    echo ""
    print_status "Useful commands:"
    echo "  Check timer status: systemctl status ${APP_NAME}.timer"
    echo "  Check service logs: journalctl -u ${APP_NAME}.service -f"
    echo "  Run manual collection: sudo -u $SERVICE_USER $VENV_DIR/bin/python $APP_DIR/collect_solar_data.py"
    echo "  Start timer: systemctl start ${APP_NAME}.timer"
    echo "  Stop timer: systemctl stop ${APP_NAME}.timer"
    echo ""
    print_success "Installation complete!"
}

main() {
    print_status "Starting Solar Inverter Data Collector installation..."

    check_root
    install_dependencies
    create_user
    setup_application_directory
    setup_python_environment
    setup_systemd_service
    setup_logrotate
    setup_database_config
    start_services
    show_status
}

# Run main function
main