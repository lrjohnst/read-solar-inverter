#!/usr/bin/env python3
"""
Database setup script for Solar Inverter Data Collector
Creates database, tables, and user if they don't exist
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
import getpass


def get_db_config():
    """Get database configuration from user input or environment variables"""
    config = {
        'host': os.getenv('DB_HOST') or input("MySQL Host (default: localhost): ").strip() or 'localhost',
        'root_user': os.getenv('DB_ROOT_USER') or input("MySQL Root Username (default: root): ").strip() or 'root',
        'root_password': os.getenv('DB_ROOT_PASSWORD') or getpass.getpass("MySQL Root Password: "),
        'app_user': os.getenv('DB_USER') or input("Application Database User (default: solar_user): ").strip() or 'solar_user',
        'app_password': os.getenv('DB_PASSWORD') or getpass.getpass("Application Database Password: "),
        'database': os.getenv('DB_NAME') or input("Database Name (default: solar_inverter): ").strip() or 'solar_inverter'
    }
    return config


def create_database_and_user(config):
    """Create database and user with proper permissions"""
    connection = None
    try:
        # Connect as root
        connection = mysql.connector.connect(
            host=config['host'],
            user=config['root_user'],
            password=config['root_password']
        )

        cursor = connection.cursor()

        print(f"Creating database '{config['database']}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']}")

        print(f"Creating user '{config['app_user']}'...")
        cursor.execute(f"CREATE USER IF NOT EXISTS '{config['app_user']}'@'%' IDENTIFIED BY '{config['app_password']}'")
        cursor.execute(f"CREATE USER IF NOT EXISTS '{config['app_user']}'@'localhost' IDENTIFIED BY '{config['app_password']}'")

        print(f"Granting permissions to '{config['app_user']}'...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON {config['database']}.* TO '{config['app_user']}'@'%'")
        cursor.execute(f"GRANT ALL PRIVILEGES ON {config['database']}.* TO '{config['app_user']}'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")

        connection.commit()
        print("Database and user created successfully!")

    except Error as e:
        print(f"Error creating database and user: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

    return True


def create_tables(config):
    """Create the required tables"""
    connection = None
    try:
        # Connect as application user
        connection = mysql.connector.connect(
            host=config['host'],
            user=config['app_user'],
            password=config['app_password'],
            database=config['database']
        )

        cursor = connection.cursor()

        print("Creating inverter_data table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inverter_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            state VARCHAR(50),
            vac_l1 DECIMAL(6,2),
            vac_l2 DECIMAL(6,2),
            vac_l3 DECIMAL(6,2),
            iac_l1 DECIMAL(6,3),
            iac_l2 DECIMAL(6,3),
            iac_l3 DECIMAL(6,3),
            freq1 DECIMAL(5,2),
            freq2 DECIMAL(5,2),
            freq3 DECIMAL(5,2),
            pac1 INT,
            pac2 INT,
            pac3 INT,
            p_ac INT,
            temp DECIMAL(4,1),
            e_today DECIMAL(8,2),
            t_today DECIMAL(6,1),
            e_total DECIMAL(12,2),
            co2 DECIMAL(12,2),
            t_total DECIMAL(12,1),
            v_pv1 DECIMAL(6,1),
            v_pv2 DECIMAL(6,1),
            v_pv3 DECIMAL(6,1),
            v_bus DECIMAL(6,1),
            max_power INT,
            i_pv11 DECIMAL(6,3),
            i_pv12 DECIMAL(6,3),
            i_pv13 DECIMAL(6,3),
            i_pv14 DECIMAL(6,3),
            i_pv21 DECIMAL(6,3),
            i_pv22 DECIMAL(6,3),
            i_pv23 DECIMAL(6,3),
            i_pv24 DECIMAL(6,3),
            i_pv31 DECIMAL(6,3),
            i_pv32 DECIMAL(6,3),
            i_pv33 DECIMAL(6,3),
            i_pv34 DECIMAL(6,3),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_timestamp (timestamp),
            INDEX idx_state (state),
            INDEX idx_created_at (created_at)
        )
        """)

        print("Creating collection_logs table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS collection_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            status ENUM('success', 'error', 'warning') NOT NULL,
            message TEXT,
            execution_time_ms INT,
            records_processed INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_timestamp (timestamp),
            INDEX idx_status (status)
        )
        """)

        connection.commit()
        print("Tables created successfully!")

        # Insert test log entry
        print("Inserting test log entry...")
        cursor.execute("""
        INSERT INTO collection_logs (timestamp, status, message, execution_time_ms)
        VALUES (NOW(), 'success', 'Database setup completed', 0)
        """)
        connection.commit()

        print("Database setup completed successfully!")

    except Error as e:
        print(f"Error creating tables: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

    return True


def create_env_file(config):
    """Create .env file with database configuration"""
    env_content = f"""# Solar Inverter Data Collector Configuration
SOLAR_XML_ENDPOINT=http://192.168.1.50/real_time_data.xml
DB_HOST={config['host']}
DB_USER={config['app_user']}
DB_PASSWORD={config['app_password']}
DB_NAME={config['database']}
REQUEST_TIMEOUT=10
LOG_LEVEL=INFO
"""

    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("Created .env file with configuration")
        return True
    except Exception as e:
        print(f"Error creating .env file: {e}")
        return False


def main():
    """Main setup function"""
    print("=== Solar Inverter Database Setup ===")
    print()

    config = get_db_config()

    print("\nSetting up database...")
    if not create_database_and_user(config):
        sys.exit(1)

    print("\nCreating tables...")
    if not create_tables(config):
        sys.exit(1)

    print("\nCreating configuration file...")
    if not create_env_file(config):
        print("Warning: Could not create .env file")

    print("\n=== Setup Complete ===")
    print(f"Database: {config['database']}")
    print(f"User: {config['app_user']}")
    print(f"Host: {config['host']}")
    print("\nYou can now run the data collector script!")


if __name__ == "__main__":
    main()