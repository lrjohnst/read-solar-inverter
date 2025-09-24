#!/usr/bin/env python3
"""
Solar Inverter Data Collector
Reads XML data from inverter endpoint and stores in MySQL database
"""

import os
import sys
import time
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional, Dict, Any
import requests
import mysql.connector
from mysql.connector import Error
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Configuration class for database and endpoint settings"""
    xml_endpoint: str = os.getenv('SOLAR_XML_ENDPOINT', 'http://192.168.1.50/real_time_data.xml')
    db_host: str = os.getenv('DB_HOST', 'localhost')
    db_user: str = os.getenv('DB_USER', 'solar_user')
    db_password: str = os.getenv('DB_PASSWORD', '')
    db_name: str = os.getenv('DB_NAME', 'solar_inverter')
    request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', '10'))
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')


def setup_logging(log_level: str) -> logging.Logger:
    """Setup logging configuration"""
    logger = logging.getLogger('solar_collector')
    logger.setLevel(getattr(logging, log_level.upper()))

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def parse_xml_value(value: str) -> Optional[float]:
    """Parse XML value, handling '-' as None"""
    if value is None or value.strip() == '-' or value.strip() == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def fetch_inverter_data(endpoint: str, timeout: int, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Fetch and parse XML data from inverter endpoint"""
    try:
        logger.debug(f"Fetching data from {endpoint}")
        response = requests.get(endpoint, timeout=timeout)
        response.raise_for_status()

        root = ET.fromstring(response.content)

        # Parse XML data according to your structure
        data = {
            'timestamp': datetime.now(),
            'state': root.find('state').text if root.find('state') is not None else None,
            'vac_l1': parse_xml_value(root.find('Vac_l1').text if root.find('Vac_l1') is not None else None),
            'vac_l2': parse_xml_value(root.find('Vac_l2').text if root.find('Vac_l2') is not None else None),
            'vac_l3': parse_xml_value(root.find('Vac_l3').text if root.find('Vac_l3') is not None else None),
            'iac_l1': parse_xml_value(root.find('Iac_l1').text if root.find('Iac_l1') is not None else None),
            'iac_l2': parse_xml_value(root.find('Iac_l2').text if root.find('Iac_l2') is not None else None),
            'iac_l3': parse_xml_value(root.find('Iac_l3').text if root.find('Iac_l3') is not None else None),
            'freq1': parse_xml_value(root.find('Freq1').text if root.find('Freq1') is not None else None),
            'freq2': parse_xml_value(root.find('Freq2').text if root.find('Freq2') is not None else None),
            'freq3': parse_xml_value(root.find('Freq3').text if root.find('Freq3') is not None else None),
            'pac1': int(parse_xml_value(root.find('pac1').text if root.find('pac1') is not None else None) or 0),
            'pac2': int(parse_xml_value(root.find('pac2').text if root.find('pac2') is not None else None) or 0) if parse_xml_value(root.find('pac2').text if root.find('pac2') is not None else None) is not None else None,
            'pac3': int(parse_xml_value(root.find('pac3').text if root.find('pac3') is not None else None) or 0) if parse_xml_value(root.find('pac3').text if root.find('pac3') is not None else None) is not None else None,
            'p_ac': int(parse_xml_value(root.find('p-ac').text if root.find('p-ac') is not None else None) or 0),
            'temp': parse_xml_value(root.find('temp').text if root.find('temp') is not None else None),
            'e_today': parse_xml_value(root.find('e-today').text if root.find('e-today') is not None else None),
            't_today': parse_xml_value(root.find('t-today').text if root.find('t-today') is not None else None),
            'e_total': parse_xml_value(root.find('e-total').text if root.find('e-total') is not None else None),
            'co2': parse_xml_value(root.find('CO2').text if root.find('CO2') is not None else None),
            't_total': parse_xml_value(root.find('t-total').text if root.find('t-total') is not None else None),
            'v_pv1': parse_xml_value(root.find('v-pv1').text if root.find('v-pv1') is not None else None),
            'v_pv2': parse_xml_value(root.find('v-pv2').text if root.find('v-pv2') is not None else None),
            'v_pv3': parse_xml_value(root.find('v-pv3').text if root.find('v-pv3') is not None else None),
            'v_bus': parse_xml_value(root.find('v-bus').text if root.find('v-bus') is not None else None),
            'max_power': int(parse_xml_value(root.find('maxPower').text if root.find('maxPower') is not None else None) or 0),
            'i_pv11': parse_xml_value(root.find('i-pv11').text if root.find('i-pv11') is not None else None),
            'i_pv12': parse_xml_value(root.find('i-pv12').text if root.find('i-pv12') is not None else None),
            'i_pv13': parse_xml_value(root.find('i-pv13').text if root.find('i-pv13') is not None else None),
            'i_pv14': parse_xml_value(root.find('i-pv14').text if root.find('i-pv14') is not None else None),
            'i_pv21': parse_xml_value(root.find('i-pv21').text if root.find('i-pv21') is not None else None),
            'i_pv22': parse_xml_value(root.find('i-pv22').text if root.find('i-pv22') is not None else None),
            'i_pv23': parse_xml_value(root.find('i-pv23').text if root.find('i-pv23') is not None else None),
            'i_pv24': parse_xml_value(root.find('i-pv24').text if root.find('i-pv24') is not None else None),
            'i_pv31': parse_xml_value(root.find('i-pv31').text if root.find('i-pv31') is not None else None),
            'i_pv32': parse_xml_value(root.find('i-pv32').text if root.find('i-pv32') is not None else None),
            'i_pv33': parse_xml_value(root.find('i-pv33').text if root.find('i-pv33') is not None else None),
            'i_pv34': parse_xml_value(root.find('i-pv34').text if root.find('i-pv34') is not None else None),
        }

        logger.debug(f"Parsed data: {data}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from endpoint: {e}")
        return None
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while fetching data: {e}")
        return None


def store_data(data: Dict[str, Any], config: Config, logger: logging.Logger) -> bool:
    """Store data in MySQL database"""
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
        INSERT INTO inverter_data (
            timestamp, state, vac_l1, vac_l2, vac_l3, iac_l1, iac_l2, iac_l3,
            freq1, freq2, freq3, pac1, pac2, pac3, p_ac, temp, e_today, t_today,
            e_total, co2, t_total, v_pv1, v_pv2, v_pv3, v_bus, max_power,
            i_pv11, i_pv12, i_pv13, i_pv14, i_pv21, i_pv22, i_pv23, i_pv24,
            i_pv31, i_pv32, i_pv33, i_pv34
        ) VALUES (
            %(timestamp)s, %(state)s, %(vac_l1)s, %(vac_l2)s, %(vac_l3)s,
            %(iac_l1)s, %(iac_l2)s, %(iac_l3)s, %(freq1)s, %(freq2)s, %(freq3)s,
            %(pac1)s, %(pac2)s, %(pac3)s, %(p_ac)s, %(temp)s, %(e_today)s,
            %(t_today)s, %(e_total)s, %(co2)s, %(t_total)s, %(v_pv1)s,
            %(v_pv2)s, %(v_pv3)s, %(v_bus)s, %(max_power)s, %(i_pv11)s,
            %(i_pv12)s, %(i_pv13)s, %(i_pv14)s, %(i_pv21)s, %(i_pv22)s,
            %(i_pv23)s, %(i_pv24)s, %(i_pv31)s, %(i_pv32)s, %(i_pv33)s, %(i_pv34)s
        )
        """

        cursor.execute(insert_query, data)
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
        logger.info("Starting solar data collection")

        # Fetch data from inverter
        data = fetch_inverter_data(config.xml_endpoint, config.request_timeout, logger)

        if data is None:
            execution_time = int((time.time() - start_time) * 1000)
            log_collection_result('error', 'Failed to fetch data from inverter', execution_time, config, logger)
            sys.exit(1)

        # Store data in database
        success = store_data(data, config, logger)

        execution_time = int((time.time() - start_time) * 1000)

        if success:
            message = f"Successfully collected data: Power={data['p_ac']}W, Temp={data['temp']}°C, Today={data['e_today']}kWh"
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