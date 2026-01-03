"""
Display Manager Module
Manages OLED/LCD display for MMDVM status information
"""

import logging
import time
from datetime import datetime
from typing import Optional, Dict
from threading import Lock

logger = logging.getLogger(__name__)

# Try to import OLED libraries (optional)
try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import ssd1306
    from PIL import ImageFont
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False
    logger.debug("Display libraries not available (luma.oled)")


class DisplayManager:
    """Manage OLED/LCD display for system status"""
    
    def __init__(self, config: dict):
        """
        Initialize Display Manager
        
        Args:
            config: Display configuration dictionary
        """
        self.enabled = config.get('enabled', False) and DISPLAY_AVAILABLE
        self.device = None
        self.font = None
        self.lock = Lock()
        
        # Status tracking
        self.status = {
            'slot1_rx': False,
            'slot2_rx': False,
            'db_connected': False,
            'api_connected': False,
            'last_dmr_data': '',
            'last_update': None
        }
        
        if self.enabled:
            try:
                # Initialize I2C display (SSD1306 128x64)
                i2c_port = config.get('i2c_port', 1)
                i2c_address = config.get('i2c_address', 0x3C)
                
                serial = i2c(port=i2c_port, address=i2c_address)
                self.device = ssd1306(serial)
                
                # Load font
                try:
                    self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 10)
                except:
                    self.font = ImageFont.load_default()
                
                logger.info(f"Display initialized (I2C port {i2c_port}, address 0x{i2c_address:02X})")
                self.show_startup_message()
                
            except Exception as e:
                logger.error(f"Failed to initialize display: {e}", exc_info=True)
                self.enabled = False
        else:
            if not DISPLAY_AVAILABLE:
                logger.info("Display disabled: libraries not available")
            else:
                logger.info("Display disabled in configuration")
    
    def show_startup_message(self):
        """Display startup message"""
        if not self.enabled:
            return
        
        try:
            with canvas(self.device) as draw:
                draw.text((10, 10), "EasyDispatch", fill="white", font=self.font)
                draw.text((10, 25), "Collector v1.0", fill="white", font=self.font)
                draw.text((10, 40), "Starting...", fill="white", font=self.font)
        except Exception as e:
            logger.error(f"Error showing startup message: {e}")
    
    def update_slot_status(self, slot: int, active: bool):
        """
        Update slot RX status
        
        Args:
            slot: Slot number (1 or 2)
            active: Whether slot is receiving
        """
        with self.lock:
            if slot == 1:
                self.status['slot1_rx'] = active
            elif slot == 2:
                self.status['slot2_rx'] = active
            self.status['last_update'] = datetime.now()
        
        self._refresh_display()
    
    def update_db_status(self, connected: bool):
        """
        Update database connection status
        
        Args:
            connected: Whether DB is connected
        """
        with self.lock:
            self.status['db_connected'] = connected
            self.status['last_update'] = datetime.now()
        
        self._refresh_display()
    
    def update_api_status(self, connected: bool):
        """
        Update API connection status
        
        Args:
            connected: Whether API is connected
        """
        with self.lock:
            self.status['api_connected'] = connected
            self.status['last_update'] = datetime.now()
        
        self._refresh_display()
    
    def show_dmr_data(self, data_string: str):
        """
        Display received DMR data string
        
        Args:
            data_string: DMR data received from network
        """
        with self.lock:
            # Truncate if too long
            self.status['last_dmr_data'] = data_string[:60]
            self.status['last_update'] = datetime.now()
        
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh the display with current status"""
        if not self.enabled:
            return
        
        try:
            with self.lock:
                slot1_status = "OK" if self.status['slot1_rx'] else "No"
                slot2_status = "OK" if self.status['slot2_rx'] else "No"
                db_status = "OK" if self.status['db_connected'] else "No"
                api_status = "OK" if self.status['api_connected'] else "No"
                dmr_data = self.status['last_dmr_data']
            
            with canvas(self.device) as draw:
                # Line 1: Slot statuses
                draw.text((0, 0), f"S1:{slot1_status} S2:{slot2_status}", fill="white", font=self.font)
                
                # Line 2: Connection statuses
                draw.text((0, 12), f"DB:{db_status} API:{api_status}", fill="white", font=self.font)
                
                # Line 3: Separator
                draw.line((0, 24, 127, 24), fill="white")
                
                # Lines 4-6: DMR data (scrolling if needed)
                if dmr_data:
                    # Split into multiple lines if needed (approximately 21 chars per line)
                    lines = []
                    for i in range(0, len(dmr_data), 21):
                        lines.append(dmr_data[i:i+21])
                    
                    y_pos = 28
                    for line in lines[:3]:  # Max 3 lines
                        draw.text((0, y_pos), line, fill="white", font=self.font)
                        y_pos += 12
                else:
                    draw.text((0, 28), "Waiting for data...", fill="white", font=self.font)
                    
        except Exception as e:
            logger.error(f"Error refreshing display: {e}")
    
    def show_error(self, message: str):
        """
        Display error message
        
        Args:
            message: Error message to display
        """
        if not self.enabled:
            return
        
        try:
            with canvas(self.device) as draw:
                draw.text((0, 10), "ERROR:", fill="white", font=self.font)
                
                # Split message into lines
                words = message.split()
                lines = []
                current_line = ""
                
                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    if len(test_line) <= 21:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
                
                y_pos = 25
                for line in lines[:3]:
                    draw.text((0, y_pos), line, fill="white", font=self.font)
                    y_pos += 12
                    
        except Exception as e:
            logger.error(f"Error showing error message: {e}")
    
    def clear(self):
        """Clear the display"""
        if not self.enabled:
            return
        
        try:
            self.device.clear()
        except Exception as e:
            logger.error(f"Error clearing display: {e}")
    
    def get_status(self) -> Dict:
        """
        Get current status
        
        Returns:
            Status dictionary
        """
        with self.lock:
            return self.status.copy()
