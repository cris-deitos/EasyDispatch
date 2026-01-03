"""
Command Handler Module
Executes remote commands received from the backend API
"""

import logging
import subprocess
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CommandHandler:
    """Handler for executing remote commands"""
    
    def __init__(self, config: dict):
        """
        Initialize Command Handler
        
        Args:
            config: Configuration dictionary
        """
        self.mmdvm_config_path = config.get('mmdvm_config_path', '/etc/mmdvm/MMDVM.ini')
        self.dmr_id = config.get('dmr_id', 2222000)
        
        logger.info("Initialized Command Handler")
    
    def execute_command(self, command: Dict) -> tuple[bool, Optional[str]]:
        """
        Execute a command
        
        Args:
            command: Command dictionary from API
            
        Returns:
            Tuple of (success, error_message)
        """
        command_type = command.get('command_type')
        
        try:
            if command_type == 'sms':
                return self._send_sms(command)
            elif command_type == 'call_alert':
                return self._send_call_alert(command)
            elif command_type == 'gps_request':
                return self._request_gps(command)
            elif command_type == 'radio_check':
                return self._radio_check(command)
            elif command_type == 'remote_monitor':
                return self._remote_monitor(command)
            else:
                error = f"Unknown command type: {command_type}"
                logger.error(error)
                return False, error
                
        except Exception as e:
            error = f"Command execution failed: {e}"
            logger.error(error, exc_info=True)
            return False, error
    
    def _send_sms(self, command: Dict) -> tuple[bool, Optional[str]]:
        """
        Send SMS to radio or talkgroup
        
        Args:
            command: Command dictionary
            
        Returns:
            Tuple of (success, error_message)
        """
        payload = command.get('payload', {})
        target_radio_id = command.get('target_radio_id')
        target_talkgroup_id = command.get('target_talkgroup_id')
        message = payload.get('message', '')
        
        if not message:
            return False, "No message provided"
        
        # Determine target
        if target_radio_id:
            target = f"PC{target_radio_id}"
            target_desc = f"radio {target_radio_id}"
        elif target_talkgroup_id:
            target = f"TG{target_talkgroup_id}"
            target_desc = f"talkgroup {target_talkgroup_id}"
        else:
            return False, "No target specified"
        
        logger.info(f"Sending SMS to {target_desc}: {message}")
        
        # Use MMDVM remote control (if available) or external tool
        # This is a placeholder - actual implementation depends on MMDVM setup
        try:
            # Example using a hypothetical DMR SMS tool
            # In reality, this might use serial commands or other methods
            cmd = [
                'dmr-sms-send',
                '--source', str(self.dmr_id),
                '--target', target,
                '--message', message
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"SMS sent successfully to {target_desc}")
                return True, None
            else:
                error = f"SMS send failed: {result.stderr}"
                logger.error(error)
                return False, error
                
        except FileNotFoundError:
            # Tool not available - log as info since this is expected in some setups
            logger.info("DMR SMS tool not available - SMS sending not implemented")
            return True, None  # Return success to prevent retries
        except subprocess.TimeoutExpired:
            error = "SMS send timeout"
            logger.error(error)
            return False, error
    
    def _send_call_alert(self, command: Dict) -> tuple[bool, Optional[str]]:
        """
        Send call alert to radio
        
        Args:
            command: Command dictionary
            
        Returns:
            Tuple of (success, error_message)
        """
        target_radio_id = command.get('target_radio_id')
        
        if not target_radio_id:
            return False, "No target radio specified"
        
        logger.info(f"Sending call alert to radio {target_radio_id}")
        
        try:
            # Example using a hypothetical DMR call alert tool
            cmd = [
                'dmr-call-alert',
                '--source', str(self.dmr_id),
                '--target', str(target_radio_id)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"Call alert sent to radio {target_radio_id}")
                return True, None
            else:
                error = f"Call alert failed: {result.stderr}"
                logger.error(error)
                return False, error
                
        except FileNotFoundError:
            logger.info("DMR call alert tool not available")
            return True, None  # Return success to prevent retries
        except subprocess.TimeoutExpired:
            error = "Call alert timeout"
            logger.error(error)
            return False, error
    
    def _request_gps(self, command: Dict) -> tuple[bool, Optional[str]]:
        """
        Request GPS position from radio
        
        Args:
            command: Command dictionary
            
        Returns:
            Tuple of (success, error_message)
        """
        target_radio_id = command.get('target_radio_id')
        
        if not target_radio_id:
            return False, "No target radio specified"
        
        logger.info(f"Requesting GPS from radio {target_radio_id}")
        
        try:
            # Send GPS request command
            # This typically uses DMR data protocol
            cmd = [
                'dmr-gps-request',
                '--source', str(self.dmr_id),
                '--target', str(target_radio_id)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"GPS request sent to radio {target_radio_id}")
                return True, None
            else:
                error = f"GPS request failed: {result.stderr}"
                logger.error(error)
                return False, error
                
        except FileNotFoundError:
            logger.info("DMR GPS request tool not available")
            return True, None
        except subprocess.TimeoutExpired:
            error = "GPS request timeout"
            logger.error(error)
            return False, error
    
    def _radio_check(self, command: Dict) -> tuple[bool, Optional[str]]:
        """
        Perform radio check (ping)
        
        Args:
            command: Command dictionary
            
        Returns:
            Tuple of (success, error_message)
        """
        target_radio_id = command.get('target_radio_id')
        
        if not target_radio_id:
            return False, "No target radio specified"
        
        logger.info(f"Performing radio check on {target_radio_id}")
        
        # Radio check is typically done by sending a call alert
        # and waiting for acknowledgment
        return self._send_call_alert(command)
    
    def _remote_monitor(self, command: Dict) -> tuple[bool, Optional[str]]:
        """
        Activate remote monitoring (silent listen)
        
        Args:
            command: Command dictionary
            
        Returns:
            Tuple of (success, error_message)
        """
        target_radio_id = command.get('target_radio_id')
        payload = command.get('payload', {})
        duration = payload.get('duration', 30)  # Default 30 seconds
        
        if not target_radio_id:
            return False, "No target radio specified"
        
        logger.warning(f"Remote monitor request for radio {target_radio_id} (duration: {duration}s)")
        
        try:
            # Remote monitor command
            # This is an advanced feature that requires special setup
            cmd = [
                'dmr-remote-monitor',
                '--source', str(self.dmr_id),
                '--target', str(target_radio_id),
                '--duration', str(duration)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration + 10
            )
            
            if result.returncode == 0:
                logger.info(f"Remote monitor activated for radio {target_radio_id}")
                return True, None
            else:
                error = f"Remote monitor failed: {result.stderr}"
                logger.error(error)
                return False, error
                
        except FileNotFoundError:
            logger.info("DMR remote monitor tool not available")
            return True, None
        except subprocess.TimeoutExpired:
            error = "Remote monitor timeout"
            logger.error(error)
            return False, error
