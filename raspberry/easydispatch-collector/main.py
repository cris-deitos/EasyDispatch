"""
EasyDispatch Collector - Main Entry Point
Monitors DMR traffic and sends data to backend API
"""

import sys
import signal
import time
import logging
import logging.config
import yaml
from pathlib import Path
from threading import Thread, Event

from collector import DMRMonitor, AudioCapture, DataParser, APIClient, CommandHandler


# Global stop event
stop_event = Event()


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)


def setup_logging(config: dict):
    """Setup logging configuration"""
    try:
        log_config_path = Path(__file__).parent / 'config' / 'logging.yaml'
        
        if log_config_path.exists():
            with open(log_config_path, 'r') as f:
                log_config = yaml.safe_load(f)
                
            # Update log file path from main config if specified
            if 'logging' in config and 'file' in config['logging']:
                log_config['handlers']['file']['filename'] = config['logging']['file']
            
            # Update log level from main config if specified
            if 'logging' in config and 'level' in config['logging']:
                log_config['root']['level'] = config['logging']['level']
            
            logging.config.dictConfig(log_config)
        else:
            # Fallback to basic config
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    except Exception as e:
        print(f"Error setting up logging: {e}")
        logging.basicConfig(level=logging.INFO)


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, shutting down...")
    stop_event.set()


class EasyDispatchCollector:
    """Main collector application"""
    
    def __init__(self, config: dict):
        """Initialize collector with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.api_client = APIClient(config['api'])
        self.audio_capture = AudioCapture(config['audio'])
        self.data_parser = DataParser()
        self.command_handler = CommandHandler({
            'mmdvm_config_path': config['mmdvm']['config_path'],
            'dmr_id': config['raspberry']['dmr_id']
        })
        
        # Track active audio recordings
        self.active_recordings = {}
        
        # Initialize DMR monitor with callback
        self.dmr_monitor = DMRMonitor(
            config['mmdvm']['log_path'],
            callback=self.handle_dmr_event
        )
        
        # Polling intervals
        self.commands_interval = config['polling']['commands_interval']
        self.status_interval = config['polling']['status_update_interval']
        self.cleanup_interval = config['polling'].get('cleanup_interval', 3600)
        
        # Background threads
        self.command_thread = None
        self.cleanup_thread = None
        
        self.logger.info("EasyDispatch Collector initialized")
    
    def start(self):
        """Start the collector"""
        self.logger.info("Starting EasyDispatch Collector...")
        
        # Start API client queue processor
        self.api_client.start_queue_processor()
        
        # Start command polling thread
        self.command_thread = Thread(target=self.command_polling_loop, daemon=True)
        self.command_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = Thread(target=self.cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        # Start DMR monitoring (blocking)
        try:
            self.dmr_monitor.start()
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the collector"""
        self.logger.info("Stopping EasyDispatch Collector...")
        
        # Stop DMR monitor
        self.dmr_monitor.stop()
        
        # Stop API client
        self.api_client.stop_queue_processor()
        
        # Set stop event for threads
        stop_event.set()
        
        self.logger.info("EasyDispatch Collector stopped")
    
    def handle_dmr_event(self, event_type: str, data: dict):
        """
        Handle DMR events from monitor
        
        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            if event_type == 'transmission_start':
                self.handle_transmission_start(data)
            elif event_type == 'transmission_end':
                self.handle_transmission_end(data)
            elif event_type == 'data_transmission':
                self.handle_data_transmission(data)
            elif event_type == 'emergency':
                self.handle_emergency(data)
        except Exception as e:
            self.logger.error(f"Error handling DMR event: {e}", exc_info=True)
    
    def handle_transmission_start(self, transmission: dict):
        """Handle start of voice transmission"""
        self.logger.info(f"Transmission started: Slot {transmission['slot']}, Radio {transmission['radio_id']}")
        
        # Start audio recording
        recording_id = self.audio_capture.start_recording(
            transmission['slot'],
            transmission['radio_id'],
            transmission['destination_id']
        )
        
        if recording_id:
            self.active_recordings[f"{transmission['slot']}_{transmission['radio_id']}"] = {
                'recording_id': recording_id,
                'transmission': transmission
            }
        
        # Update radio status to online
        self.api_client.post_radio_status(
            transmission['radio_id'],
            'online',
            transmission.get('rssi'),
            transmission.get('ber')
        )
    
    def handle_transmission_end(self, transmission: dict):
        """Handle end of voice transmission"""
        self.logger.info(f"Transmission ended: Slot {transmission['slot']}, Duration {transmission['duration']}s")
        
        # Stop audio recording
        key = f"{transmission['slot']}_{transmission['radio_id']}"
        if key in self.active_recordings:
            recording_info = self.active_recordings[key]
            recording_id = recording_info['recording_id']
            
            audio_file = self.audio_capture.stop_recording(recording_id)
            
            # Post transmission to API
            self.api_client.post_transmission(transmission, audio_file)
            
            del self.active_recordings[key]
        else:
            # Post transmission without audio
            self.api_client.post_transmission(transmission)
    
    def handle_data_transmission(self, data: dict):
        """Handle data transmission (SMS, GPS, etc.)"""
        self.logger.info(f"Data transmission: Slot {data['slot']}, Radio {data['radio_id']}")
        
        # Try to parse as SMS
        # Note: In real implementation, raw data would be available from MMDVM
        # This is a simplified example
        
        # For now, just log it
        # In production, you would parse the actual data payload
    
    def handle_emergency(self, emergency: dict):
        """Handle emergency alert"""
        self.logger.warning(f"EMERGENCY: Slot {emergency['slot']}")
        
        # Find the radio ID from current transmissions
        # In real implementation, this would be parsed from the emergency packet
        
        emergency_data = {
            'radio_id': 0,  # Would be parsed from packet
            'emergency_type': 'emergency_button',
            'triggered_at': emergency['timestamp']
        }
        
        self.api_client.post_emergency(emergency_data)
    
    def command_polling_loop(self):
        """Poll for pending commands from API"""
        self.logger.info("Started command polling loop")
        
        while not stop_event.is_set():
            try:
                # Get pending commands
                commands = self.api_client.get_pending_commands()
                
                for command in commands:
                    command_id = command['id']
                    self.logger.info(f"Executing command {command_id}: {command['command_type']}")
                    
                    # Execute command
                    success, error_message = self.command_handler.execute_command(command)
                    
                    # Post result
                    status = 'completed' if success else 'failed'
                    self.api_client.post_command_result(command_id, status, error_message)
                
            except Exception as e:
                self.logger.error(f"Error in command polling: {e}", exc_info=True)
            
            # Wait before next poll
            stop_event.wait(self.commands_interval)
    
    def cleanup_loop(self):
        """Periodic cleanup of old audio files"""
        self.logger.info("Started cleanup loop")
        
        while not stop_event.is_set():
            try:
                self.audio_capture.cleanup_old_files(max_age_hours=24)
            except Exception as e:
                self.logger.error(f"Error in cleanup: {e}", exc_info=True)
            
            # Wait before next cleanup
            stop_event.wait(self.cleanup_interval)


def main():
    """Main entry point"""
    # Determine config path
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = Path(__file__).parent / 'config' / 'config.yaml'
    
    # Check if config exists
    if not Path(config_path).exists():
        print(f"Configuration file not found: {config_path}")
        print("Please create config.yaml from config.yaml.example")
        sys.exit(1)
    
    # Load configuration
    config = load_config(config_path)
    
    # Setup logging
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("EasyDispatch Collector Starting")
    logger.info("=" * 60)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start collector
    collector = EasyDispatchCollector(config)
    collector.start()


if __name__ == '__main__':
    main()
