# Solar Inverter Data Collector

A Python-based system for collecting real-time data from solar inverters and storing it in a MySQL database. This system runs entirely in user space and automatically collects data every minute, creating a comprehensive time-series dataset of your solar inverter's performance.

## Features

- **Real-time Data Collection**: Fetches XML data from your solar inverter every minute
- **MySQL Storage**: Stores all data in a structured MySQL database for analysis
- **User-Space Installation**: Runs as your user, no root privileges required for operation
- **Systemd User Services**: Automatic data collection via systemd user timer
- **Easy Configuration**: Environment-based configuration with `.env` file
- **Simple Deployment**: Git-based deployment with automatic updates
- **Monitoring Tools**: Built-in status monitoring and statistics
- **Error Handling**: Robust error handling with detailed logging

## System Requirements

- Linux server (Raspberry Pi OS, Ubuntu 18.04+ recommended)
- Python 3.6+
- MySQL 5.7+ or MariaDB 10.3+ (can be remote)
- Network access to your solar inverter
- Git for deployment updates

## Quick Start

### 1. Initial Setup

Clone this repository to your Linux machine:

```bash
git clone https://github.com/your-username/read-solar-inverter.git
cd read-solar-inverter
```

### 2. Run Installation

Make the installation script executable and run it (do NOT use sudo):

```bash
chmod +x install.sh
./install.sh
```

The installation script will:
- Install system dependencies (Python, MariaDB client) using sudo when needed
- Set up the application in `~/solar-inverter/`
- Create a Python virtual environment with isolated dependencies
- Install Python dependencies (requests, mysql-connector-python, python-dotenv)
- Configure systemd user service and timer
- Set up log rotation via cron
- Guide you through database configuration
- Create `.env` file with your settings

**Note**: The script may prompt for your sudo password to install system packages, but the application itself runs as your user.

### 3. Configure Your Environment

After installation, you may need to update the configuration:

```bash
# Edit the configuration file
nano ~/solar-inverter/.env
```

Update these settings for your setup:
```env
SOLAR_XML_ENDPOINT=http://192.168.2.21/real_time_data.xml  # Your inverter IP
DB_HOST=your-mysql-server.com  # Your remote MySQL server
DB_USER=solar_user
DB_PASSWORD=your_password
DB_NAME=solar_inverter
```

### 4. Enable Auto-Start After Reboot

To ensure the service starts after server reboots:

```bash
sudo loginctl enable-linger $USER
```

### 5. Verify Installation

Check if the service is running:

```bash
systemctl --user status solar-inverter-collector.timer
```

Or use the monitoring script:

```bash
~/solar-inverter/monitor.sh status
```

Test manual data collection:

```bash
~/solar-inverter/venv/bin/python ~/solar-inverter/collect_solar_data.py
```

## Configuration

### Environment Variables

The system uses environment variables for configuration. These are stored in `~/solar-inverter/.env`:

```bash
SOLAR_XML_ENDPOINT=http://192.168.2.21/real_time_data.xml  # Your inverter endpoint
DB_HOST=your-mysql-server.com  # Your remote MySQL server
DB_USER=solar_user
DB_PASSWORD=your_password
DB_NAME=solar_inverter
REQUEST_TIMEOUT=10
LOG_LEVEL=INFO
```

### Updating Configuration

You can edit the configuration at any time:

```bash
nano ~/solar-inverter/.env
```

Changes take effect on the next data collection cycle (within a minute) or restart the service:

```bash
systemctl --user restart solar-inverter-collector.timer
```

### Finding Your Inverter Endpoint

Test if you can reach your inverter:

```bash
curl http://192.168.2.21/real_time_data.xml
```

This should return XML data similar to your inverter's real-time information.

## Database Schema

The system creates two main tables:

### `inverter_data`
Stores the actual solar inverter readings:
- Timestamp and state information
- AC/DC voltage and current readings
- Power output (individual phases and total)
- Energy production (daily and total)
- Temperature readings
- PV string voltages and currents

### `collection_logs`
Tracks the data collection process:
- Collection timestamps
- Success/error status
- Error messages
- Execution time metrics

## Monitoring and Management

### Monitor Script

Use the built-in monitoring script:

```bash
# Check service status
~/solar-inverter/monitor.sh status

# View recent logs
~/solar-inverter/monitor.sh logs

# Follow logs in real-time
~/solar-inverter/monitor.sh follow

# View collection statistics
~/solar-inverter/monitor.sh stats

# Test data collection
~/solar-inverter/monitor.sh test

# Start/stop/restart service
~/solar-inverter/monitor.sh start
~/solar-inverter/monitor.sh stop
~/solar-inverter/monitor.sh restart
```

### Manual Data Collection

You can run data collection manually for testing:

```bash
~/solar-inverter/venv/bin/python ~/solar-inverter/collect_solar_data.py
```

### Service Management

User systemd commands:

```bash
# Check timer status
systemctl --user status solar-inverter-collector.timer

# Check service status
systemctl --user status solar-inverter-collector.service

# View logs
journalctl --user -u solar-inverter-collector.service -f

# Start/stop timer
systemctl --user start solar-inverter-collector.timer
systemctl --user stop solar-inverter-collector.timer

# Enable/disable automatic startup
systemctl --user enable solar-inverter-collector.timer
systemctl --user disable solar-inverter-collector.timer
```

## Easy Updates and Deployment

### Simple Git-Based Updates

The easiest way to update your installation:

```bash
cd ~/Documenten/read-solar-inverter  # Your repository directory
git pull                             # Get latest changes
./deploy.sh update                   # Deploy to ~/solar-inverter
```

This approach:
- Uses HTTPS (no SSH keys needed)
- Automatically stops service, updates files, restarts service
- Creates automatic backups
- Tests the deployment

### Manual Deployment Options

```bash
# From your repository directory
cd ~/Documenten/read-solar-inverter

# Update to latest version
./deploy.sh update

# Rollback to previous version (if something goes wrong)
./deploy.sh rollback
```

### GitHub Actions Setup (Optional)

For fully automated deployments, you can set up GitHub Actions:

1. **Add Repository Secrets** in your GitHub repository settings:
   - `PROD_HOST`: Your server IP/hostname
   - `PROD_USER`: SSH username
   - `PROD_SSH_KEY`: Private SSH key
   - `PROD_PORT`: SSH port (optional, defaults to 22)

2. **Automatic Deployment**: Pushes to `main` branch will auto-deploy

**Note**: Most users prefer the simple `git pull && ./deploy.sh update` approach.

## Data Analysis

Once data is being collected, you can analyze it using SQL queries:

### Basic Statistics

```sql
-- Daily energy production
SELECT DATE(timestamp) as date,
       MAX(e_today) as daily_energy_kwh,
       MAX(p_ac) as peak_power_w,
       AVG(temp) as avg_temperature_c
FROM inverter_data
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Hourly power averages
SELECT DATE(timestamp) as date,
       HOUR(timestamp) as hour,
       AVG(p_ac) as avg_power_w,
       COUNT(*) as readings
FROM inverter_data
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND p_ac > 0
GROUP BY DATE(timestamp), HOUR(timestamp)
ORDER BY date DESC, hour;
```

### Performance Monitoring

```sql
-- Collection success rate
SELECT DATE(timestamp) as date,
       COUNT(*) as total_attempts,
       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
       ROUND(100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate_percent
FROM collection_logs
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

## Troubleshooting

### Common Issues

1. **Service not starting**:
   ```bash
   journalctl --user -u solar-inverter-collector.service -f
   # or
   ~/solar-inverter/monitor.sh logs
   ```

2. **Database connection errors**:
   - Check MySQL server connectivity
   - Verify credentials in `~/solar-inverter/.env` file
   - Test connection manually: `~/solar-inverter/venv/bin/python ~/solar-inverter/collect_solar_data.py`

3. **XML endpoint not accessible**:
   - Verify network connectivity to inverter
   - Check inverter IP address in `~/solar-inverter/.env`
   - Test with curl: `curl http://192.168.2.21/real_time_data.xml`

4. **Configuration not loading**:
   - Ensure `.env` file exists: `ls -la ~/solar-inverter/.env`
   - Check file contents: `cat ~/solar-inverter/.env`
   - The script uses `python-dotenv` to load environment variables

5. **Service not starting after reboot**:
   ```bash
   # Enable lingering for your user
   sudo loginctl enable-linger $USER
   ```

### Log Locations

- Service logs: `journalctl --user -u solar-inverter-collector.service`
- Monitor script: `~/solar-inverter/monitor.sh logs`
- Manual test: `~/solar-inverter/venv/bin/python ~/solar-inverter/collect_solar_data.py`

## Data Backup

### Database Backup

Set up regular MySQL backups:

```bash
# Create backup script
cat > /etc/cron.daily/solar-backup << 'EOF'
#!/bin/bash
mysqldump -h your-mysql-host -u backup_user -p'password' solar_inverter > /backup/solar-inverter-$(date +%Y%m%d).sql
find /backup/ -name "solar-inverter-*.sql" -mtime +30 -delete
EOF

chmod +x /etc/cron.daily/solar-backup
```

## Security Considerations

- The application runs as your user account with minimal system impact
- Database credentials are stored in environment variables (`.env` file)
- The `.env` file is excluded from version control via `.gitignore`
- Uses Python virtual environment for dependency isolation
- HTTPS-based git updates (no SSH keys required)
- Regular security updates should be applied to the host system

## File Structure

After installation, your system will have:

```
~/solar-inverter/              # Installation directory
├── collect_solar_data.py      # Main data collection script
├── setup_database.py          # Database setup utility
├── monitor.sh                 # Monitoring and management script
├── requirements.txt           # Python dependencies
├── .env                       # Configuration (not in git)
├── venv/                      # Python virtual environment
└── logs/                      # Application logs (if created)

~/Documenten/read-solar-inverter/  # Repository directory
├── All source files           # Your cloned repository
└── .git/                      # Git repository data
```

**Note**: Always run updates from the repository directory, not the installation directory.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on a development system
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs for error messages
3. Open an issue in the GitHub repository

---

## Summary of Key Changes

This system has been designed for **simplicity and user-friendliness**:

- ✅ **No root required**: Runs entirely in user space
- ✅ **Simple installation**: One script, no complex setup
- ✅ **Easy updates**: `git pull && ./deploy.sh update`
- ✅ **Clean removal**: `rm -rf ~/solar-inverter` removes everything
- ✅ **No system pollution**: Virtual environment keeps dependencies isolated
- ✅ **Raspberry Pi ready**: Works great on Raspberry Pi OS

**Quick Commands Reference**:
```bash
# Check status
~/solar-inverter/monitor.sh status

# View logs
~/solar-inverter/monitor.sh logs

# Update system
cd ~/Documenten/read-solar-inverter && git pull && ./deploy.sh update

# Test manually
~/solar-inverter/venv/bin/python ~/solar-inverter/collect_solar_data.py
```

**Note**: Update the repository URL in `deploy.sh` with your actual repository URL if using automated deployments.