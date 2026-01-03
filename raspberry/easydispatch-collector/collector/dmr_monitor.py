"""
DMR Monitor Module
Monitors MMDVM log files in real-time to detect DMR transmissions
"""

import re
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Callable

logger = logging.getLogger(__name__)


class DMRMonitor:
    """Monitor DMR traffic from MMDVMHost logs"""
    
    # Regex patterns for log parsing
    PATTERNS = {
        'voice_header': re.compile(
            r'M:\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+DMR Slot (\d+),\s+received voice header from (\d+) to (TG|PC) (\d+)'
        ),
        'voice_end': re.compile(
            r'M:\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+DMR Slot (\d+),\s+received voice end of transmission,\s+(\d+\.\d+)s,\s+BER: (\d+\.\d+)%'
        ),
        'rssi': re.compile(
            r'DMR Slot (\d+),\s+.*?RSSI:\s+(-?\d+)'
        ),
        'data_header': re.compile(
            r'M:\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+DMR Slot (\d+),\s+received data header from (\d+) to (TG|PC) (\d+)'
        ),
        'gps_data': re.compile(
            r'DMR Slot (\d+),.*?GPS data'
        ),
        'emergency': re.compile(
            r'M:\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+DMR Slot (\d+),.*?Emergency'
        ),
    }
    
    def __init__(self, log_path: str, callback: Optional[Callable] = None):
        """
        Initialize DMR Monitor
        
        Args:
            log_path: Path to MMDVM log file
            callback: Callback function for transmission events
        """
        self.log_path = Path(log_path)
        self.callback = callback
        self.running = False
        self.current_transmissions = {}  # Track ongoing transmissions
        
        logger.info(f"Initialized DMR Monitor for log: {log_path}")
    
    def start(self):
        """Start monitoring the log file"""
        self.running = True
        logger.info("Starting DMR monitoring...")
        
        try:
            self._monitor_log()
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
            self.stop()
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}", exc_info=True)
            self.stop()
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        logger.info("DMR monitoring stopped")
    
    def _monitor_log(self):
        """Main monitoring loop using tail-like functionality"""
        
        # Wait for log file to exist
        while not self.log_path.exists() and self.running:
            logger.warning(f"Log file not found: {self.log_path}, waiting...")
            time.sleep(5)
        
        if not self.running:
            return
        
        logger.info(f"Monitoring log file: {self.log_path}")
        
        with open(self.log_path, 'r') as f:
            # Seek to end of file
            f.seek(0, 2)
            
            while self.running:
                line = f.readline()
                
                if not line:
                    # No new data, wait a bit
                    time.sleep(0.1)
                    continue
                
                # Process the line
                self._process_line(line.strip())
    
    def _process_line(self, line: str):
        """Process a single log line"""
        
        # Check for voice header (start of transmission)
        match = self.PATTERNS['voice_header'].search(line)
        if match:
            self._handle_voice_header(match)
            return
        
        # Check for voice end (end of transmission)
        match = self.PATTERNS['voice_end'].search(line)
        if match:
            self._handle_voice_end(match)
            return
        
        # Check for RSSI updates
        match = self.PATTERNS['rssi'].search(line)
        if match:
            self._handle_rssi(match)
            return
        
        # Check for data header
        match = self.PATTERNS['data_header'].search(line)
        if match:
            self._handle_data_header(match)
            return
        
        # Check for emergency
        match = self.PATTERNS['emergency'].search(line)
        if match:
            self._handle_emergency(match)
            return
    
    def _handle_voice_header(self, match):
        """Handle voice transmission start"""
        timestamp_str, slot, radio_id, dest_type, dest_id = match.groups()
        
        slot = int(slot)
        radio_id = int(radio_id)
        dest_id = int(dest_id)
        
        key = f"{slot}_{radio_id}"
        
        transmission = {
            'type': 'voice',
            'slot': slot,
            'radio_id': radio_id,
            'destination_type': dest_type,
            'destination_id': dest_id,
            'start_time': self._parse_timestamp(timestamp_str),
            'rssi': None,
            'ber': None,
        }
        
        self.current_transmissions[key] = transmission
        
        logger.info(f"Voice transmission started: Slot {slot}, Radio {radio_id} -> {dest_type} {dest_id}")
        
        # Trigger callback for transmission start
        if self.callback:
            self.callback('transmission_start', transmission)
    
    def _handle_voice_end(self, match):
        """Handle voice transmission end"""
        timestamp_str, slot, duration, ber = match.groups()
        
        slot = int(slot)
        duration = float(duration)
        ber = float(ber)
        
        # Find the transmission in current_transmissions
        for key, transmission in list(self.current_transmissions.items()):
            if transmission['slot'] == slot and transmission['type'] == 'voice':
                transmission['end_time'] = self._parse_timestamp(timestamp_str)
                transmission['duration'] = duration
                transmission['ber'] = ber
                
                logger.info(f"Voice transmission ended: Slot {slot}, Duration {duration}s, BER {ber}%")
                
                # Trigger callback for transmission end
                if self.callback:
                    self.callback('transmission_end', transmission)
                
                # Remove from current transmissions
                del self.current_transmissions[key]
                break
    
    def _handle_rssi(self, match):
        """Handle RSSI update"""
        slot, rssi = match.groups()
        
        slot = int(slot)
        rssi = int(rssi)
        
        # Update RSSI in current transmission
        for transmission in self.current_transmissions.values():
            if transmission['slot'] == slot:
                transmission['rssi'] = rssi
                break
    
    def _handle_data_header(self, match):
        """Handle data transmission start"""
        timestamp_str, slot, radio_id, dest_type, dest_id = match.groups()
        
        slot = int(slot)
        radio_id = int(radio_id)
        dest_id = int(dest_id)
        
        data_transmission = {
            'type': 'data',
            'slot': slot,
            'radio_id': radio_id,
            'destination_type': dest_type,
            'destination_id': dest_id,
            'timestamp': self._parse_timestamp(timestamp_str),
        }
        
        logger.info(f"Data transmission: Slot {slot}, Radio {radio_id} -> {dest_type} {dest_id}")
        
        # Trigger callback for data transmission
        if self.callback:
            self.callback('data_transmission', data_transmission)
    
    def _handle_emergency(self, match):
        """Handle emergency alert"""
        timestamp_str, slot = match.groups()
        
        slot = int(slot)
        
        emergency = {
            'type': 'emergency',
            'slot': slot,
            'timestamp': self._parse_timestamp(timestamp_str),
        }
        
        logger.warning(f"EMERGENCY detected on Slot {slot}!")
        
        # Trigger callback for emergency
        if self.callback:
            self.callback('emergency', emergency)
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse MMDVM log timestamp"""
        try:
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            # Fallback to current time if parsing fails
            logger.warning(f"Failed to parse timestamp: {timestamp_str}")
            return datetime.now()
