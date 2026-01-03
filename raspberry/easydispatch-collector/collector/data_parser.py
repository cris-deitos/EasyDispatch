"""
Data Parser Module
Parses DMR data messages (SMS, GPS, Emergency, etc.)
"""

import re
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DataParser:
    """Parse DMR data transmissions"""
    
    # SMS message patterns
    SMS_PATTERN = re.compile(r'Short Data.*?:(.+)', re.IGNORECASE)
    
    # GPS coordinate patterns (APRS-style)
    GPS_PATTERN = re.compile(
        r'(\d{2})(\d{2}\.\d{2})([NS])/(\d{3})(\d{2}\.\d{2})([EW])'
    )
    
    # GPS with altitude
    GPS_ALT_PATTERN = re.compile(
        r'(\d{2})(\d{2}\.\d{2})([NS])/(\d{3})(\d{2}\.\d{2})([EW])/A=(\d{6})'
    )
    
    def __init__(self):
        """Initialize Data Parser"""
        logger.info("Initialized Data Parser")
    
    def parse_sms(self, data: bytes) -> Optional[Dict]:
        """
        Parse SMS from DMR short data
        
        Args:
            data: Raw data bytes
            
        Returns:
            Dictionary with SMS information or None
        """
        try:
            # Try to decode as text
            text = data.decode('utf-8', errors='ignore').strip()
            
            if not text:
                return None
            
            # Remove control characters
            text = ''.join(char for char in text if char.isprintable() or char.isspace())
            
            if len(text) < 1:
                return None
            
            logger.info(f"Parsed SMS: {text}")
            
            return {
                'message': text,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to parse SMS: {e}", exc_info=True)
            return None
    
    def parse_gps(self, data: bytes) -> Optional[Dict]:
        """
        Parse GPS coordinates from DMR data
        
        Args:
            data: Raw data bytes
            
        Returns:
            Dictionary with GPS information or None
        """
        try:
            # Try to decode as text
            text = data.decode('utf-8', errors='ignore')
            
            # Try with altitude first
            match = self.GPS_ALT_PATTERN.search(text)
            if match:
                lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir, alt_feet = match.groups()
                
                latitude = self._convert_to_decimal(lat_deg, lat_min, lat_dir)
                longitude = self._convert_to_decimal(lon_deg, lon_min, lon_dir)
                altitude = int(alt_feet) * 0.3048  # Convert feet to meters
                
                logger.info(f"Parsed GPS with altitude: {latitude}, {longitude}, {altitude}m")
                
                return {
                    'latitude': latitude,
                    'longitude': longitude,
                    'altitude': int(altitude),
                    'timestamp': datetime.now()
                }
            
            # Try without altitude
            match = self.GPS_PATTERN.search(text)
            if match:
                lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = match.groups()
                
                latitude = self._convert_to_decimal(lat_deg, lat_min, lat_dir)
                longitude = self._convert_to_decimal(lon_deg, lon_min, lon_dir)
                
                logger.info(f"Parsed GPS: {latitude}, {longitude}")
                
                return {
                    'latitude': latitude,
                    'longitude': longitude,
                    'altitude': None,
                    'timestamp': datetime.now()
                }
            
            # Try to parse as raw decimal coordinates
            decimal_match = re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', text)
            if decimal_match:
                latitude = float(decimal_match.group(1))
                longitude = float(decimal_match.group(2))
                
                # Validate range
                if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                    logger.info(f"Parsed GPS (decimal): {latitude}, {longitude}")
                    return {
                        'latitude': latitude,
                        'longitude': longitude,
                        'altitude': None,
                        'timestamp': datetime.now()
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse GPS: {e}", exc_info=True)
            return None
    
    def _convert_to_decimal(self, degrees: str, minutes: str, direction: str) -> float:
        """
        Convert GPS coordinates from degrees/minutes to decimal
        
        Args:
            degrees: Degrees as string
            minutes: Minutes as string (with decimal)
            direction: N/S/E/W
            
        Returns:
            Decimal coordinate
        """
        decimal = float(degrees) + float(minutes) / 60.0
        
        if direction in ['S', 'W']:
            decimal = -decimal
        
        return round(decimal, 6)
    
    def parse_emergency(self, data: bytes) -> Optional[Dict]:
        """
        Parse emergency alert data
        
        Args:
            data: Raw data bytes
            
        Returns:
            Dictionary with emergency information or None
        """
        try:
            # Emergency alerts usually just indicate the type
            text = data.decode('utf-8', errors='ignore').strip().lower()
            
            emergency_types = {
                'emergency': 'emergency_button',
                'panic': 'panic',
                'fire': 'fire',
                'medical': 'medical',
                'help': 'help',
                'sos': 'sos'
            }
            
            emergency_type = 'generic'
            for keyword, etype in emergency_types.items():
                if keyword in text:
                    emergency_type = etype
                    break
            
            logger.warning(f"Parsed emergency: {emergency_type}")
            
            return {
                'emergency_type': emergency_type,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to parse emergency: {e}", exc_info=True)
            return {
                'emergency_type': 'generic',
                'timestamp': datetime.now()
            }
    
    def parse_telemetry(self, data: bytes) -> Optional[Dict]:
        """
        Parse telemetry data (battery, temperature, etc.)
        
        Args:
            data: Raw data bytes
            
        Returns:
            Dictionary with telemetry information or None
        """
        try:
            # This is a placeholder for future telemetry parsing
            # Different radio manufacturers use different formats
            
            text = data.decode('utf-8', errors='ignore')
            
            telemetry = {}
            
            # Try to extract battery voltage
            battery_match = re.search(r'BATT[:\s]*(\d+\.?\d*)V?', text, re.IGNORECASE)
            if battery_match:
                telemetry['battery_voltage'] = float(battery_match.group(1))
            
            # Try to extract temperature
            temp_match = re.search(r'TEMP[:\s]*(-?\d+\.?\d*)C?', text, re.IGNORECASE)
            if temp_match:
                telemetry['temperature'] = float(temp_match.group(1))
            
            if telemetry:
                telemetry['timestamp'] = datetime.now()
                logger.info(f"Parsed telemetry: {telemetry}")
                return telemetry
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse telemetry: {e}", exc_info=True)
            return None
