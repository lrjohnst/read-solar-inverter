# Solar Inverter Data Collector

A Python-based system for collecting real-time data from solar inverters and storing it in a MySQL database. This system is designed to run on Linux machines and automatically collects data every minute, creating a comprehensive time-series dataset of your solar inverter's performance.

## Features

- **Real-time Data Collection**: Fetches XML data from your solar inverter every minute
- **MySQL Storage**: Stores all data in a structured MySQL database for analysis
- **Automatic Monitoring**: Runs as a systemd service with automatic restarts
- **Comprehensive Logging**: Tracks collection success/failure with detailed logs
- **Easy Deployment**: GitHub Actions integration for automatic deployments
- **Monitoring Tools**: Built-in status monitoring and statistics
- **Error Handling**: Robust error handling with retry logic

## System Requirements

- Linux server (Ubuntu 18.04+ recommended)
- Python 3.6+
- MySQL 5.7+ or MariaDB 10.3+
- Network access to your solar inverter
- Root/sudo access for installation

## Quick Start

### 1. Initial Setup

Clone this repository to your Linux machine:

```bash
git clone https://github.com/your-username/read-solar-inverter.git
cd read-solar-inverter
```

### 2. Run Installation

Make the installation script executable and run it:

```bash
chmod +x install.sh
sudo ./install.sh
```

The installation script will:
- Install system dependencies (Python, MySQL client, cron)
- Create a dedicated system user (`solar`)
- Set up the application in `/opt/solar-inverter/`
- Create a Python virtual environment
- Install Python dependencies
- Configure systemd service and timer
- Set up log rotation
- Guide you through database configuration

### 3. Configure Database

During installation, you'll be prompted to configure the MySQL database connection. You'll need:
- MySQL server host (your remote MySQL server)
- MySQL root credentials (for initial setup)
- Desired application database name
- Application database user credentials

### 4. Verify Installation

Check if the service is running:

```bash
sudo systemctl status solar-inverter-collector.timer
```

Monitor the logs:

```bash
sudo journalctl -u solar-inverter-collector.service -f
```

## Configuration

### Environment Variables

The system uses environment variables for configuration. These are stored in `/opt/solar-inverter/.env`:

```bash
SOLAR_XML_ENDPOINT=http://192.168.1.50/real_time_data.xml
DB_HOST=your-mysql-server.com
DB_USER=solar_user
DB_PASSWORD=your_password
DB_NAME=solar_inverter
REQUEST_TIMEOUT=10
LOG_LEVEL=INFO
```

### XML Endpoint

Update the `SOLAR_XML_ENDPOINT` in your `.env` file to match your inverter's IP address and path.

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
sudo /opt/solar-inverter/monitor.sh status

# View recent logs
sudo /opt/solar-inverter/monitor.sh logs

# Follow logs in real-time
sudo /opt/solar-inverter/monitor.sh follow

# View collection statistics
sudo /opt/solar-inverter/monitor.sh stats

# Test data collection
sudo /opt/solar-inverter/monitor.sh test

# Start/stop/restart service
sudo /opt/solar-inverter/monitor.sh start
sudo /opt/solar-inverter/monitor.sh stop
sudo /opt/solar-inverter/monitor.sh restart
```

### Manual Data Collection

You can run data collection manually for testing:

```bash
sudo -u solar /opt/solar-inverter/venv/bin/python /opt/solar-inverter/collect_solar_data.py
```

### Service Management

Standard systemd commands:

```bash
# Check timer status
sudo systemctl status solar-inverter-collector.timer

# Check service status
sudo systemctl status solar-inverter-collector.service

# View logs
sudo journalctl -u solar-inverter-collector.service -f

# Start/stop timer
sudo systemctl start solar-inverter-collector.timer
sudo systemctl stop solar-inverter-collector.timer

# Enable/disable automatic startup
sudo systemctl enable solar-inverter-collector.timer
sudo systemctl disable solar-inverter-collector.timer
```

## Automated Deployment

### GitHub Actions Setup

This repository includes GitHub Actions for automated deployment. To set it up:

1. **Add Repository Secrets** in your GitHub repository settings:
   - `PROD_HOST`: Your production server IP/hostname
   - `PROD_USER`: SSH username on production server
   - `PROD_SSH_KEY`: Private SSH key for authentication
   - `PROD_PORT`: SSH port (optional, defaults to 22)

2. **Set up SSH Key Authentication** on your production server:
   ```bash
   # On your local machine, generate a key pair
   ssh-keygen -t rsa -b 4096 -C "github-deploy"

   # Copy public key to production server
   ssh-copy-id -i ~/.ssh/id_rsa.pub user@your-server.com

   # Add the private key to GitHub secrets as PROD_SSH_KEY
   ```

3. **Automatic Deployment**: Pushes to the `main` branch will automatically deploy to production

### Manual Deployment

For manual deployments, use the deployment script:

```bash
# Initial setup on production server
sudo ./deploy.sh setup

# Update to latest version
sudo ./deploy.sh update

# Rollback to previous version
sudo ./deploy.sh rollback
```

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
   sudo journalctl -u solar-inverter-collector.service -f
   ```

2. **Database connection errors**:
   - Check MySQL server connectivity
   - Verify credentials in `.env` file
   - Check MySQL server logs

3. **XML endpoint not accessible**:
   - Verify network connectivity to inverter
   - Check inverter IP address
   - Test with curl: `curl http://192.168.1.50/real_time_data.xml`

4. **Permission issues**:
   ```bash
   sudo chown -R solar:solar /opt/solar-inverter/
   ```

### Log Locations

- Service logs: `journalctl -u solar-inverter-collector.service`
- Application logs: `/var/log/syslog` (search for 'solar-collector')
- Deployment logs: GitHub Actions logs in repository

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

- The application runs as a dedicated `solar` user with minimal privileges
- Database credentials are stored in environment variables
- SSH keys are used for deployment authentication
- Log rotation prevents disk space issues
- Regular security updates should be applied to the host system

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

**Note**: Update the repository URL in `deploy.sh` and GitHub Actions workflow with your actual repository URL before using the automated deployment features.