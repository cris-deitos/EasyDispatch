"""
API Client Module
Handles communication with the hosting backend API
"""

import requests
import logging
import time
import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from queue import Queue, Empty
from threading import Thread, Event

logger = logging.getLogger(__name__)


class APIClient:
    """Client for communicating with EasyDispatch backend API"""
    
    def __init__(self, config: dict):
        """
        Initialize API Client
        
        Args:
            config: API configuration dictionary
        """
        self.endpoint = config.get('endpoint')
        self.api_key = config.get('key')
        self.timeout = config.get('timeout', 30)
        self.retry_attempts = config.get('retry_attempts', 3)
        self.raspberry_id = config.get('raspberry_id', 'UNKNOWN')
        
        # Offline queue for failed requests
        self.offline_queue = Queue()
        self.queue_file = Path('/var/lib/easydispatch/offline_queue.json')
        
        # Background thread for queue processing
        self.queue_thread = None
        self.stop_event = Event()
        
        # Load offline queue from disk
        self._load_offline_queue()
        
        logger.info(f"Initialized API Client (endpoint: {self.endpoint})")
    
    def start_queue_processor(self):
        """Start background thread for processing offline queue"""
        if self.queue_thread is None or not self.queue_thread.is_alive():
            self.stop_event.clear()
            self.queue_thread = Thread(target=self._process_offline_queue, daemon=True)
            self.queue_thread.start()
            logger.info("Started offline queue processor")
    
    def stop_queue_processor(self):
        """Stop background queue processor"""
        if self.queue_thread and self.queue_thread.is_alive():
            self.stop_event.set()
            self.queue_thread.join(timeout=5)
            logger.info("Stopped offline queue processor")
    
    def post_transmission(self, transmission: Dict, audio_file: Optional[Path] = None) -> bool:
        """
        Post voice transmission to API
        
        Args:
            transmission: Transmission data dictionary
            audio_file: Path to audio file (optional)
            
        Returns:
            True if successful, False otherwise
        """
        endpoint = f"{self.endpoint}/transmissions"
        
        data = {
            'radio_id': transmission.get('radio_id'),
            'talkgroup_id': transmission.get('destination_id'),
            'timeslot': transmission.get('slot'),
            'start_time': self._format_datetime(transmission.get('start_time')),
            'end_time': self._format_datetime(transmission.get('end_time')),
            'duration': transmission.get('duration'),
            'rssi': transmission.get('rssi'),
            'ber': transmission.get('ber'),
        }
        
        files = None
        if audio_file and audio_file.exists():
            files = {'audio': open(audio_file, 'rb')}
        
        try:
            response = self._make_request('POST', endpoint, data=data, files=files)
            
            if files:
                files['audio'].close()
            
            if response and response.get('success'):
                logger.info(f"Transmission posted successfully: {response.get('transmission_id')}")
                return True
            else:
                logger.error(f"Failed to post transmission: {response}")
                self._queue_for_retry('transmission', data, audio_file)
                return False
                
        except Exception as e:
            logger.error(f"Error posting transmission: {e}", exc_info=True)
            if files:
                files['audio'].close()
            self._queue_for_retry('transmission', data, audio_file)
            return False
    
    def post_sms(self, sms: Dict) -> bool:
        """
        Post SMS message to API
        
        Args:
            sms: SMS data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        endpoint = f"{self.endpoint}/sms"
        
        data = {
            'from_radio_id': sms.get('from_radio_id'),
            'to_radio_id': sms.get('to_radio_id'),
            'to_talkgroup_id': sms.get('to_talkgroup_id'),
            'message': sms.get('message'),
            'timestamp': self._format_datetime(sms.get('timestamp')),
        }
        
        response = self._make_request('POST', endpoint, data=data)
        
        if response and response.get('success'):
            logger.info(f"SMS posted successfully: {response.get('sms_id')}")
            return True
        else:
            logger.error(f"Failed to post SMS: {response}")
            self._queue_for_retry('sms', data)
            return False
    
    def post_gps(self, gps: Dict) -> bool:
        """
        Post GPS position to API
        
        Args:
            gps: GPS data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        endpoint = f"{self.endpoint}/gps"
        
        data = {
            'radio_id': gps.get('radio_id'),
            'latitude': gps.get('latitude'),
            'longitude': gps.get('longitude'),
            'altitude': gps.get('altitude'),
            'speed': gps.get('speed'),
            'heading': gps.get('heading'),
            'accuracy': gps.get('accuracy'),
            'timestamp': self._format_datetime(gps.get('timestamp')),
        }
        
        response = self._make_request('POST', endpoint, data=data)
        
        if response and response.get('success'):
            logger.info(f"GPS position posted successfully")
            return True
        else:
            logger.error(f"Failed to post GPS: {response}")
            self._queue_for_retry('gps', data)
            return False
    
    def post_emergency(self, emergency: Dict) -> bool:
        """
        Post emergency alert to API
        
        Args:
            emergency: Emergency data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        endpoint = f"{self.endpoint}/emergencies"
        
        data = {
            'radio_id': emergency.get('radio_id'),
            'emergency_type': emergency.get('emergency_type'),
            'latitude': emergency.get('latitude'),
            'longitude': emergency.get('longitude'),
            'triggered_at': self._format_datetime(emergency.get('triggered_at')),
        }
        
        response = self._make_request('POST', endpoint, data=data)
        
        if response and response.get('success'):
            logger.warning(f"Emergency posted successfully: {response.get('emergency_id')}")
            return True
        else:
            logger.error(f"Failed to post emergency: {response}")
            self._queue_for_retry('emergency', data)
            return False
    
    def post_radio_status(self, radio_id: int, status: str, rssi: Optional[int] = None, ber: Optional[float] = None) -> bool:
        """
        Post radio status update to API
        
        Args:
            radio_id: DMR radio ID
            status: Status (online/offline/emergency)
            rssi: Signal strength (optional)
            ber: Bit error rate (optional)
            
        Returns:
            True if successful, False otherwise
        """
        endpoint = f"{self.endpoint}/radio-status"
        
        data = {
            'radio_id': radio_id,
            'status': status,
            'rssi': rssi,
            'ber': ber,
        }
        
        response = self._make_request('POST', endpoint, data=data)
        
        if response and response.get('success'):
            return True
        else:
            logger.error(f"Failed to post radio status: {response}")
            return False
    
    def get_pending_commands(self) -> List[Dict]:
        """
        Get pending commands from API
        
        Returns:
            List of command dictionaries
        """
        endpoint = f"{self.endpoint}/commands?raspberry_id={self.raspberry_id}"
        
        response = self._make_request('GET', endpoint)
        
        if response and 'commands' in response:
            commands = response['commands']
            logger.info(f"Retrieved {len(commands)} pending commands")
            return commands
        else:
            return []
    
    def post_command_result(self, command_id: int, status: str, error_message: Optional[str] = None) -> bool:
        """
        Post command execution result to API
        
        Args:
            command_id: Command ID
            status: Execution status (completed/failed)
            error_message: Error message if failed
            
        Returns:
            True if successful, False otherwise
        """
        endpoint = f"{self.endpoint}/commands/{command_id}/complete"
        
        data = {
            'status': status,
            'error_message': error_message,
        }
        
        response = self._make_request('POST', endpoint, data=data)
        
        if response and response.get('success'):
            logger.info(f"Command result posted: {command_id} -> {status}")
            return True
        else:
            logger.error(f"Failed to post command result: {response}")
            return False
    
    def _make_request(self, method: str, url: str, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method (GET/POST)
            url: Request URL
            data: Request data
            files: Files to upload
            
        Returns:
            Response JSON or None
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        for attempt in range(self.retry_attempts):
            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, timeout=self.timeout)
                elif method == 'POST':
                    if files:
                        response = requests.post(url, headers=headers, data=data, files=files, timeout=self.timeout)
                    else:
                        headers['Content-Type'] = 'application/json'
                        response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
                else:
                    logger.error(f"Unsupported method: {method}")
                    return None
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logger.error("API authentication failed (401)")
                    return None
                else:
                    logger.warning(f"API request failed: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.retry_attempts})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error (attempt {attempt + 1}/{self.retry_attempts})")
            except Exception as e:
                logger.error(f"Request error: {e}", exc_info=True)
            
            # Wait before retry
            if attempt < self.retry_attempts - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _queue_for_retry(self, item_type: str, data: Dict, audio_file: Optional[Path] = None):
        """Queue failed request for later retry"""
        item = {
            'type': item_type,
            'data': data,
            'audio_file': str(audio_file) if audio_file else None,
            'timestamp': datetime.now().isoformat()
        }
        
        self.offline_queue.put(item)
        self._save_offline_queue()
        logger.info(f"Queued {item_type} for retry (queue size: {self.offline_queue.qsize()})")
    
    def _process_offline_queue(self):
        """Process offline queue in background"""
        while not self.stop_event.is_set():
            try:
                # Try to process one item
                item = self.offline_queue.get(timeout=10)
                
                item_type = item['type']
                data = item['data']
                audio_file = Path(item['audio_file']) if item['audio_file'] else None
                
                success = False
                
                if item_type == 'transmission':
                    success = self.post_transmission(data, audio_file)
                elif item_type == 'sms':
                    success = self.post_sms(data)
                elif item_type == 'gps':
                    success = self.post_gps(data)
                elif item_type == 'emergency':
                    success = self.post_emergency(data)
                
                if not success:
                    # Put back in queue
                    self.offline_queue.put(item)
                    time.sleep(60)  # Wait before retrying
                else:
                    self._save_offline_queue()
                    
            except Empty:
                # Queue is empty, continue
                pass
            except Exception as e:
                logger.error(f"Error processing offline queue: {e}", exc_info=True)
                time.sleep(10)
    
    def _save_offline_queue(self):
        """Save offline queue to disk"""
        try:
            items = []
            temp_queue = Queue()
            
            while not self.offline_queue.empty():
                try:
                    item = self.offline_queue.get_nowait()
                    items.append(item)
                    temp_queue.put(item)
                except Empty:
                    break
            
            # Restore queue
            while not temp_queue.empty():
                self.offline_queue.put(temp_queue.get())
            
            # Save to file
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.queue_file, 'w') as f:
                json.dump(items, f)
                
        except Exception as e:
            logger.error(f"Failed to save offline queue: {e}", exc_info=True)
    
    def _load_offline_queue(self):
        """Load offline queue from disk"""
        try:
            if self.queue_file.exists():
                with open(self.queue_file, 'r') as f:
                    items = json.load(f)
                    for item in items:
                        self.offline_queue.put(item)
                logger.info(f"Loaded {len(items)} items from offline queue")
        except Exception as e:
            logger.error(f"Failed to load offline queue: {e}", exc_info=True)
    
    def _format_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Format datetime for API"""
        if dt:
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return None
