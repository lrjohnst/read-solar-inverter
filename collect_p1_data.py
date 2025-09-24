#!/usr/bin/env python3
"""
P1 Meter Data Collector
Reads JSON data from P1 meter endpoint and stores in MySQL database
"""

import os
import sys
import time
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
import requests
import mysql.connector
from mysql.connector import Error
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Configuration class for database and endpoint settings"""
    p1_endpoint: str = os.getenv('P1_ENDPOINT', 'http://192.168.2.26/api/v1/data')
    db_host: str = os.getenv('DB_HOST', 'localhost')
    db_user: str = os.getenv('DB_USER', 'solar_user')
    db_password: str = os.getenv('DB_PASSWORD', '')
    db_name: str = os.getenv('DB_NAME', 'solar_inverter')
    request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', '10'))
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')


def setup_logging(log_level: str) -> logging.Logger:
    """Setup logging configuration"""
    logger = logging.getLogger('p1_collector')
    logger.setLevel(getattr(logging, log_level.upper()))

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def fetch_p1_data(endpoint: str, timeout: int, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Fetch and parse JSON data from P1 meter endpoint"""
    try:
        logger.debug(f"Fetching data from {endpoint}")
        response = requests.get(endpoint, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        data['timestamp'] = datetime.now()

        logger.debug(f"Parsed data: {data}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from endpoint: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while fetching data: {e}")
        return None


def get_or_create_device(data: Dict[str, Any], config: Config, logger: logging.Logger) -> Optional[int]:
    """Get existing device ID or create new device entry"""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=config.db_host,
            user=config.db_user,
            password=config.db_password,
            database=config.db_name
        )

        cursor = connection.cursor()

        # Check if device exists
        select_query = "SELECT id FROM p1_devices WHERE unique_id = %s"
        cursor.execute(select_query, (data['unique_id'],))
        result = cursor.fetchone()

        if result:
            return result[0]

        # Create new device
        insert_query = """
        INSERT INTO p1_devices (unique_id, meter_model, smr_version, wifi_ssid)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            data['unique_id'],
            data.get('meter_model'),
            data.get('smr_version'),
            data.get('wifi_ssid')
        ))
        connection.commit()

        device_id = cursor.lastrowid
        logger.info(f"Created new P1 device: {data.get('meter_model')} (ID: {device_id})")
        return device_id

    except Error as e:
        logger.error(f"Database error while managing device: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while managing device: {e}")
        return None
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def store_data(data: Dict[str, Any], device_id: int, config: Config, logger: logging.Logger) -> bool:
    """Store P1 meter data in MySQL database"""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=config.db_host,
            user=config.db_user,
            password=config.db_password,
            database=config.db_name
        )

        cursor = connection.cursor()

        insert_query = """
        INSERT INTO p1_meter_data (
            device_id, timestamp, wifi_strength, active_tariff,
            total_power_import_kwh, total_power_import_t1_kwh, total_power_import_t2_kwh,
            total_power_export_kwh, total_power_export_t1_kwh, total_power_export_t2_kwh,
            active_power_w, active_power_l1_w, active_power_l2_w, active_power_l3_w,
            active_voltage_l1_v, active_voltage_l2_v, active_voltage_l3_v,
            active_current_a, active_current_l1_a, active_current_l2_a, active_current_l3_a,
            voltage_sag_l1_count, voltage_sag_l2_count, voltage_sag_l3_count,
            voltage_swell_l1_count, voltage_swell_l2_count, voltage_swell_l3_count,
            any_power_fail_count, long_power_fail_count
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        values = (
            device_id,
            data['timestamp'],
            data.get('wifi_strength'),
            data.get('active_tariff'),
            data.get('total_power_import_kwh'),
            data.get('total_power_import_t1_kwh'),
            data.get('total_power_import_t2_kwh'),
            data.get('total_power_export_kwh'),
            data.get('total_power_export_t1_kwh'),
            data.get('total_power_export_t2_kwh'),
            data.get('active_power_w'),
            data.get('active_power_l1_w'),
            data.get('active_power_l2_w'),
            data.get('active_power_l3_w'),
            data.get('active_voltage_l1_v'),
            data.get('active_voltage_l2_v'),
            data.get('active_voltage_l3_v'),
            data.get('active_current_a'),
            data.get('active_current_l1_a'),
            data.get('active_current_l2_a'),
            data.get('active_current_l3_a'),
            data.get('voltage_sag_l1_count', 0),
            data.get('voltage_sag_l2_count', 0),
            data.get('voltage_sag_l3_count', 0),
            data.get('voltage_swell_l1_count', 0),
            data.get('voltage_swell_l2_count', 0),
            data.get('voltage_swell_l3_count', 0),
            data.get('any_power_fail_count', 0),
            data.get('long_power_fail_count', 0)
        )

        cursor.execute(insert_query, values)
        connection.commit()

        logger.debug(f"Data stored successfully, row ID: {cursor.lastrowid}")
        return True

    except Error as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while storing data: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def log_collection_result(status: str, message: str, execution_time: int, config: Config, logger: logging.Logger):
    """Log collection result to database"""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=config.db_host,
            user=config.db_user,
            password=config.db_password,
            database=config.db_name
        )

        cursor = connection.cursor()

        insert_query = """
        INSERT INTO collection_logs (timestamp, status, message, execution_time_ms)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(insert_query, (datetime.now(), status, message, execution_time))
        connection.commit()

    except Error as e:
        logger.error(f"Failed to log collection result: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def main():
    """Main execution function"""
    config = Config()
    logger = setup_logging(config.log_level)

    start_time = time.time()

    try:
        logger.info("Starting P1 meter data collection")

        # Fetch data from P1 meter
        data = fetch_p1_data(config.p1_endpoint, config.request_timeout, logger)

        if data is None:
            execution_time = int((time.time() - start_time) * 1000)
            log_collection_result('error', 'Failed to fetch data from P1 meter', execution_time, config, logger)
            sys.exit(1)

        # Get or create device
        device_id = get_or_create_device(data, config, logger)
        if device_id is None:
            execution_time = int((time.time() - start_time) * 1000)
            log_collection_result('error', 'Failed to get/create device', execution_time, config, logger)
            sys.exit(1)

        # Store data in database
        success = store_data(data, device_id, config, logger)

        execution_time = int((time.time() - start_time) * 1000)

        if success:
            message = f"Successfully collected P1 data: Power={data.get('active_power_w')}W, Tariff={data.get('active_tariff')}, Import={data.get('total_power_import_kwh')}kWh"
            logger.info(message)
            log_collection_result('success', message, execution_time, config, logger)
        else:
            log_collection_result('error', 'Failed to store data in database', execution_time, config, logger)
            sys.exit(1)

    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg)
        log_collection_result('error', error_msg, execution_time, config, logger)
        sys.exit(1)


if __name__ == "__main__":
    main()