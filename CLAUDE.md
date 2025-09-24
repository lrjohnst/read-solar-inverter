# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based solar inverter data collection system that runs in user space on Linux systems (particularly Raspberry Pi). The system fetches XML data from solar inverters via HTTP and stores time-series data in a remote MySQL database every minute.

## Architecture

**Data Flow**: Solar Inverter XML endpoint → Python collector → MySQL database
**Execution**: Systemd user timer runs `collect_solar_data.py` every minute
**Configuration**: Environment variables loaded from `.env` file using python-dotenv
**Installation**: User-space deployment to `~/solar-inverter/` with Python virtual environment

### Key Components

- **collect_solar_data.py**: Main data collector that fetches XML, parses inverter metrics, and stores in MySQL
- **setup_database.py**: Interactive database setup that creates schema and `.env` configuration
- **database_schema.sql**: MySQL schema with `inverter_data` (time-series metrics) and `collection_logs` (execution tracking)
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

# Check environment loading
cd ~/solar-inverter && python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('SOLAR_XML_ENDPOINT'))"
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

**XML Parsing**: The collector handles the specific inverter XML format with fields like `p-ac`, `e-today`, `v-pv1`, etc. Uses `parse_xml_value()` to handle `-` as null values.

**Database Schema**: Designed for time-series analysis with indexed timestamps. The `inverter_data` table captures all inverter metrics, while `collection_logs` tracks execution success/failure.

**User-Space Design**: Everything runs as the current user with systemd user services. No root privileges required for operation, only for system package installation.

**Error Handling**: Robust error handling with database logging of collection attempts, timeouts, and failures.

**Virtual Environment**: Python dependencies are isolated in `~/solar-inverter/venv/` to avoid system pollution.

## Repository vs Installation Distinction

**Repository Directory** (`~/Documenten/read-solar-inverter/`): Contains source code, used for development and deployment
**Installation Directory** (`~/solar-inverter/`): Contains running application with `.env`, logs, and venv

Always run deployment commands from the repository directory, not the installation directory.