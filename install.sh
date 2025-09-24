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
APP_DIR="$HOME/solar-inverter"
SERVICE_USER="$USER"
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

check_requirements() {
    if [[ -z "$USER" || -z "$HOME" ]]; then
        print_error "USER and HOME environment variables must be set"
        exit 1
    fi

    print_status "Installing to: $APP_DIR"
    print_status "Running as user: $SERVICE_USER"
}

install_dependencies() {
    print_status "Installing system dependencies..."

    # Check if we need sudo for package installation
    if command -v apt-get >/dev/null 2>&1; then
        if [[ $EUID -ne 0 ]]; then
            print_status "Installing packages with sudo..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv cron mysql-client
        else
            apt-get update
            apt-get install -y python3 python3-pip python3-venv cron mysql-client
        fi
    elif command -v yum >/dev/null 2>&1; then
        if [[ $EUID -ne 0 ]]; then
            sudo yum install -y python3 python3-pip mysql
        else
            yum install -y python3 python3-pip mysql
        fi
    else
        print_warning "Package manager not detected. Please install: python3, python3-pip, python3-venv, mysql-client"
    fi

    print_success "System dependencies installed"
}

setup_application_directory() {
    print_status "Setting up application directory..."

    # Create directory structure
    mkdir -p "$APP_DIR"/{logs,config}

    # Copy application files
    cp -r . "$APP_DIR/"

    # Set permissions
    chmod +x "$APP_DIR/collect_solar_data.py"
    chmod +x "$APP_DIR/setup_database.py"
    chmod +x "$APP_DIR/monitor.sh"

    print_success "Application directory setup complete"
}

setup_python_environment() {
    print_status "Setting up Python virtual environment..."

    # Create virtual environment
    python3 -m venv "$VENV_DIR"

    # Install Python dependencies
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

    print_success "Python environment setup complete"
}

setup_systemd_service() {
    print_status "Setting up systemd user service..."

    # Create user systemd directory
    mkdir -p "$HOME/.config/systemd/user"

    cat > "$HOME/.config/systemd/user/${APP_NAME}.service" << EOF
[Unit]
Description=Solar Inverter Data Collector
After=network.target

[Service]
Type=oneshot
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python collect_solar_data.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

    # Setup systemd timer for every minute execution
    cat > "$HOME/.config/systemd/user/${APP_NAME}.timer" << EOF
[Unit]
Description=Run Solar Inverter Data Collector every minute
Requires=${APP_NAME}.service

[Timer]
OnCalendar=*:*:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Reload and enable user services
    systemctl --user daemon-reload
    systemctl --user enable ${APP_NAME}.timer

    print_success "Systemd user service and timer created"
}

setup_logrotate() {
    print_status "Setting up log rotation..."

    # Try to setup system logrotate, fallback to user script
    if [[ $EUID -eq 0 ]]; then
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
        print_success "System log rotation configured"
    else
        # Create a simple log cleanup script for the user
        cat > "$APP_DIR/cleanup_logs.sh" << EOF
#!/bin/bash
find "$APP_DIR/logs" -name "*.log" -mtime +30 -delete 2>/dev/null || true
EOF
        chmod +x "$APP_DIR/cleanup_logs.sh"

        # Add to user crontab if possible
        if command -v crontab >/dev/null 2>&1; then
            (crontab -l 2>/dev/null || echo "") | grep -v "$APP_DIR/cleanup_logs.sh" | { cat; echo "0 2 * * * $APP_DIR/cleanup_logs.sh"; } | crontab -
            print_success "User log rotation configured via cron"
        else
            print_warning "Log cleanup script created at $APP_DIR/cleanup_logs.sh (run manually or add to cron)"
        fi
    fi
}

setup_database_config() {
    print_status "Setting up database configuration..."

    # Run database setup
    print_status "Please configure the database..."
    "$VENV_DIR/bin/python" "$APP_DIR/setup_database.py"

    print_success "Database configuration complete"
}

start_services() {
    print_status "Starting services..."

    systemctl --user start ${APP_NAME}.timer
    systemctl --user status ${APP_NAME}.timer --no-pager -l

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
    echo "  Check timer status: systemctl --user status ${APP_NAME}.timer"
    echo "  Check service logs: journalctl --user -u ${APP_NAME}.service -f"
    echo "  Run manual collection: $VENV_DIR/bin/python $APP_DIR/collect_solar_data.py"
    echo "  Start timer: systemctl --user start ${APP_NAME}.timer"
    echo "  Stop timer: systemctl --user stop ${APP_NAME}.timer"
    echo "  Monitor script: $APP_DIR/monitor.sh status"
    echo ""
    print_success "Installation complete!"
}

main() {
    print_status "Starting Solar Inverter Data Collector installation..."

    check_requirements
    install_dependencies
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