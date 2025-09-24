# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based energy monitoring system that collects data from both solar inverters and P1 smart meters. It runs in user space on Linux systems (particularly Raspberry Pi). The system fetches XML data from solar inverters and JSON data from P1 meters via HTTP, storing comprehensive time-series data in a remote MySQL database every minute.

## Architecture

**Data Flow**:
- Solar Inverter XML endpoint → Python collector → MySQL database
- P1 Smart Meter JSON endpoint → Python collector → MySQL database
**Execution**: Systemd user timer runs `collect_solar_data.py` every minute (collects both solar and P1 data)
**Configuration**: Environment variables loaded from `.env` file using python-dotenv
**Installation**: User-space deployment to `~/solar-inverter/` with Python virtual environment

### Key Components

- **collect_solar_data.py**: Main data collector that fetches XML (solar inverter) and JSON (P1 meter) data, and stores both in MySQL
- **collect_p1_data.py**: Standalone P1 meter collector (legacy - functionality integrated into main collector)
- **setup_database.py**: Interactive database setup that creates schema and `.env` configuration
- **database_schema.sql**: MySQL schema with multiple tables for comprehensive energy monitoring
- **install.sh**: User-space installation script that sets up systemd user services and Python venv
- **deploy.sh**: Git-based deployment script for updates (uses `git pull` from current repo)
- **monitor.sh**: Service management and monitoring utility

### Configuration System

The system uses environment-based configuration with automatic detection:
- **Development/Repo**: Configuration happens in repository directory during setup
- **Production/Install**: Configuration is deployed to `~/solar-inverter/.env`
- **Auto-detection**: Scripts detect installation directory vs repository directory context

## Common Commands

### Installation and Setup
```bash
# Initial installation (from repository directory)
./install.sh

# Database setup (interactive)
~/solar-inverter/venv/bin/python ~/solar-inverter/setup_database.py

# Update configuration
nano ~/solar-inverter/.env
```

### Development and Testing
```bash
# Test data collection manually
~/solar-inverter/venv/bin/python ~/solar-inverter/collect_solar_data.py

# Test XML endpoint connectivity
curl http://192.168.2.21/real_time_data.xml

# Test P1 meter endpoint connectivity
curl http://192.168.2.26/api/v1/data

# Check environment loading
cd ~/solar-inverter && python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(f'Solar: {os.getenv(\"SOLAR_XML_ENDPOINT\")}, P1: {os.getenv(\"P1_ENDPOINT\")}')"
```

### Service Management
```bash
# Service status and logs
~/solar-inverter/monitor.sh status
~/solar-inverter/monitor.sh logs

# Manual service control
systemctl --user start/stop/restart solar-inverter-collector.timer
journalctl --user -u solar-inverter-collector.service -f
```

### Deployment
```bash
# Update installation (from repository directory)
git pull && ./deploy.sh update

# Rollback if needed
./deploy.sh rollback
```

## Development Notes

**Data Collection**:
- **XML Parsing**: Handles solar inverter XML format with fields like `p-ac`, `e-today`, `v-pv1`, etc. Uses `parse_xml_value()` to handle `-` as null values.
- **JSON Parsing**: Handles P1 smart meter JSON format with comprehensive energy metrics including phase-level data and tariff information.
- **Dual Collection**: Single script collects from both sources; P1 collection is optional (skipped if `P1_ENDPOINT` not configured).

**Database Schema**:
- **Solar Tables**: `inverter_data` for time-series solar metrics
- **P1 Tables**: `p1_devices` (device registration) and `p1_meter_data` (time-series measurements) with normalized device references
- **System Tables**: `collection_logs` tracks execution success/failure for both collection types
- **Optimized Storage**: P1 device info stored once, referenced by measurements to save space

**User-Space Design**: Everything runs as the current user with systemd user services. No root privileges required for operation, only for system package installation.

**Error Handling**: Robust error handling with database logging of collection attempts, timeouts, and failures. Independent error handling for solar and P1 collection.

**Virtual Environment**: Python dependencies are isolated in `~/solar-inverter/venv/` to avoid system pollution.

## Repository vs Installation Distinction

**Repository Directory** (`~/Documenten/read-solar-inverter/`): Contains source code, used for development and deployment
**Installation Directory** (`~/solar-inverter/`): Contains running application with `.env`, logs, and venv

Always run deployment commands from the repository directory, not the installation directory.