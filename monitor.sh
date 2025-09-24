#!/bin/bash

# Solar Inverter Data Collector Monitoring Script
# This script provides monitoring and management commands

APP_NAME="solar-inverter-collector"
SERVICE_USER="$USER"
APP_DIR="$HOME/solar-inverter"

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

show_status() {
    print_status "Service Status:"
    systemctl --user status ${APP_NAME}.timer --no-pager -l
    echo ""
    systemctl --user status ${APP_NAME}.service --no-pager -l
}

show_logs() {
    print_status "Recent logs (last 50 lines):"
    journalctl --user -u ${APP_NAME}.service -n 50 --no-pager
}

follow_logs() {
    print_status "Following logs (Ctrl+C to exit):"
    journalctl --user -u ${APP_NAME}.service -f
}

test_connection() {
    print_status "Testing database connection and XML endpoint..."
    "$APP_DIR/venv/bin/python" "$APP_DIR/collect_solar_data.py"
}

start_service() {
    print_status "Starting service..."
    systemctl --user start ${APP_NAME}.timer
    print_success "Service started"
    show_status
}

stop_service() {
    print_status "Stopping service..."
    systemctl --user stop ${APP_NAME}.timer
    print_success "Service stopped"
    show_status
}

restart_service() {
    print_status "Restarting service..."
    systemctl --user stop ${APP_NAME}.timer
    systemctl --user start ${APP_NAME}.timer
    print_success "Service restarted"
    show_status
}

show_stats() {
    print_status "Collection Statistics:"

    if command -v mysql &> /dev/null; then
        # Load database config from .env file if it exists
        if [[ -f "$APP_DIR/.env" ]]; then
            source "$APP_DIR/.env"
        fi

        if [[ -n "$DB_HOST" && -n "$DB_USER" && -n "$DB_PASSWORD" && -n "$DB_NAME" ]]; then
            mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" << EOF
SELECT 'Total Records' as Metric, COUNT(*) as Value FROM inverter_data
UNION ALL
SELECT 'Records Today', COUNT(*) FROM inverter_data WHERE DATE(timestamp) = CURDATE()
UNION ALL
SELECT 'Latest Power (W)', COALESCE(p_ac, 0) FROM inverter_data ORDER BY timestamp DESC LIMIT 1
UNION ALL
SELECT 'Latest Energy Today (kWh)', COALESCE(e_today, 0) FROM inverter_data ORDER BY timestamp DESC LIMIT 1
UNION ALL
SELECT 'Latest Total Energy (kWh)', COALESCE(e_total, 0) FROM inverter_data ORDER BY timestamp DESC LIMIT 1
UNION ALL
SELECT 'Success Rate Today (%)',
       ROUND(100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM collection_logs WHERE DATE(timestamp) = CURDATE();
EOF
        else
            print_warning "Database configuration not found in $APP_DIR/.env"
        fi
    else
        print_warning "MySQL client not available for statistics"
    fi
}

show_help() {
    echo "Solar Inverter Data Collector Monitor"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  status      Show service status"
    echo "  logs        Show recent logs"
    echo "  follow      Follow logs in real-time"
    echo "  start       Start the collection service"
    echo "  stop        Stop the collection service"
    echo "  restart     Restart the collection service"
    echo "  test        Test database connection and data collection"
    echo "  stats       Show collection statistics"
    echo "  help        Show this help message"
}

case "${1:-status}" in
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    follow)
        follow_logs
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    test)
        test_connection
        ;;
    stats)
        show_stats
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