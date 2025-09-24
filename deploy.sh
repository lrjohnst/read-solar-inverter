#!/bin/bash

# Manual Deployment Script for Solar Inverter Data Collector
# Use this for manual deployments or initial setup on the production server

set -e

# Configuration
REPO_URL="https://github.com/your-username/read-solar-inverter.git"
APP_DIR="$HOME/solar-inverter"
SERVICE_NAME="solar-inverter-collector"
SERVICE_USER="$USER"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
}

initial_setup() {
    print_status "Performing initial setup..."

    # Clone repository
    if [ ! -d "$APP_DIR" ]; then
        print_status "Cloning repository for initial setup..."
        git clone "$REPO_URL" /tmp/solar-setup
        cd /tmp/solar-setup
        chmod +x install.sh
        ./install.sh
        rm -rf /tmp/solar-setup
        print_success "Initial setup completed"
    else
        print_status "Application directory exists, performing update..."
        update_deployment
    fi
}

update_deployment() {
    print_status "Starting deployment update..."

    # Create temporary directory for new code
    DEPLOY_DIR="/tmp/solar-deploy-$(date +%s)"

    # Clone the repository
    print_status "Downloading latest code..."
    git clone --depth 1 "$REPO_URL" "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"

    # Stop the service during deployment
    print_status "Stopping service..."
    systemctl --user stop ${SERVICE_NAME}.timer || true

    # Backup current installation
    if [ -d "$APP_DIR" ]; then
        print_status "Creating backup..."
        cp -r "$APP_DIR" "${APP_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Update application files (preserve .env, logs, and venv)
    print_status "Updating application files..."

    # Copy new files
    cp collect_solar_data.py "$APP_DIR/"
    cp setup_database.py "$APP_DIR/"
    cp requirements.txt "$APP_DIR/"
    cp monitor.sh "$APP_DIR/"
    chmod +x "$APP_DIR"/*.py "$APP_DIR"/*.sh

    # Update Python dependencies
    print_status "Updating Python dependencies..."
    "$APP_DIR/venv/bin/pip" install --upgrade pip
    "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

    # Reload systemd and start service
    print_status "Starting service..."
    systemctl --user daemon-reload
    systemctl --user start ${SERVICE_NAME}.timer

    # Verify deployment
    print_status "Verifying deployment..."
    sleep 5

    if systemctl --user is-active --quiet ${SERVICE_NAME}.timer; then
        print_success "Service is running"
    else
        print_error "Service failed to start"
        systemctl --user status ${SERVICE_NAME}.timer --no-pager -l
        exit 1
    fi

    # Test data collection
    print_status "Testing data collection..."
    if timeout 30 "$APP_DIR/venv/bin/python" "$APP_DIR/collect_solar_data.py"; then
        print_success "Test collection successful"
    else
        print_warning "Test collection failed, but deployment completed"
    fi

    # Cleanup
    print_status "Cleaning up..."
    rm -rf "$DEPLOY_DIR"

    print_success "Deployment completed successfully!"

    # Show status
    print_status "Service status:"
    systemctl --user status ${SERVICE_NAME}.timer --no-pager -l
}

rollback() {
    print_status "Rolling back to previous version..."

    # Find latest backup
    LATEST_BACKUP=$(ls -td ${APP_DIR}.backup.* 2>/dev/null | head -1)

    if [ -z "$LATEST_BACKUP" ]; then
        print_error "No backup found for rollback"
        exit 1
    fi

    print_status "Rolling back to: $LATEST_BACKUP"

    # Stop service
    systemctl --user stop ${SERVICE_NAME}.timer || true

    # Backup current (failed) version
    mv "$APP_DIR" "${APP_DIR}.failed.$(date +%Y%m%d_%H%M%S)"

    # Restore backup
    mv "$LATEST_BACKUP" "$APP_DIR"

    # Start service
    systemctl --user start ${SERVICE_NAME}.timer

    print_success "Rollback completed"
    systemctl --user status ${SERVICE_NAME}.timer --no-pager -l
}

show_help() {
    echo "Solar Inverter Data Collector Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup       Perform initial installation"
    echo "  update      Update to latest version"
    echo "  rollback    Rollback to previous version"
    echo "  help        Show this help message"
    echo ""
    echo "Note: This script runs as the current user"
}

# Main execution
case "${1:-update}" in
    setup)
        check_requirements
        initial_setup
        ;;
    update)
        check_requirements
        update_deployment
        ;;
    rollback)
        check_requirements
        rollback
        ;;
    help)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac