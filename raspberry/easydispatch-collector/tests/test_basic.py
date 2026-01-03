#!/usr/bin/env python3
"""
Basic unit tests for EasyDispatch collector
Tests display manager, API client, and audio management
"""

import sys
import os
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

# Add collector to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collector.display_manager import DisplayManager
from collector.api_client import APIClient
from collector.audio_capture import AudioCapture


class TestDisplayManager(unittest.TestCase):
    """Test Display Manager functionality"""
    
    def setUp(self):
        """Set up test display manager"""
        self.config = {
            'enabled': False  # Disable actual display for testing
        }
        self.display = DisplayManager(self.config)
    
    def test_initialization(self):
        """Test display manager initializes correctly"""
        self.assertIsNotNone(self.display)
        self.assertFalse(self.display.enabled)
    
    def test_status_tracking(self):
        """Test status tracking"""
        self.display.update_slot_status(1, True)
        status = self.display.get_status()
        self.assertTrue(status['slot1_rx'])
        
        self.display.update_slot_status(2, False)
        status = self.display.get_status()
        self.assertFalse(status['slot2_rx'])
    
    def test_connection_status(self):
        """Test connection status updates"""
        self.display.update_api_status(True)
        self.display.update_db_status(True)
        
        status = self.display.get_status()
        self.assertTrue(status['api_connected'])
        self.assertTrue(status['db_connected'])
    
    def test_dmr_data_display(self):
        """Test DMR data display"""
        test_data = "RX S1: 2222000 -> TG1"
        self.display.show_dmr_data(test_data)
        
        status = self.display.get_status()
        self.assertEqual(status['last_dmr_data'], test_data)


class TestAPIClient(unittest.TestCase):
    """Test API Client functionality"""
    
    def setUp(self):
        """Set up test API client"""
        self.config = {
            'endpoint': 'https://example.com/api/v1',
            'key': 'test_api_key',
            'timeout': 5,
            'retry_attempts': 1,
            'raspberry_id': 'TEST001'
        }
        self.client = APIClient(self.config)
    
    def test_initialization(self):
        """Test API client initializes correctly"""
        self.assertIsNotNone(self.client)
        self.assertEqual(self.client.endpoint, self.config['endpoint'])
        self.assertEqual(self.client.api_key, self.config['key'])
    
    def test_format_datetime(self):
        """Test datetime formatting"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        formatted = self.client._format_datetime(dt)
        self.assertEqual(formatted, '2024-01-01 12:00:00')
    
    def test_format_none_datetime(self):
        """Test formatting None datetime"""
        formatted = self.client._format_datetime(None)
        self.assertIsNone(formatted)


class TestAudioCapture(unittest.TestCase):
    """Test Audio Capture functionality"""
    
    def setUp(self):
        """Set up test audio capture"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'capture_device': 'plughw:0,0',
            'sample_rate': 8000,
            'format': 'wav',
            'compression': 'mp3',
            'bitrate': 64,
            'recording_dir': self.temp_dir
        }
        self.audio = AudioCapture(self.config)
    
    def tearDown(self):
        """Clean up temporary directory"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test audio capture initializes correctly"""
        self.assertIsNotNone(self.audio)
        self.assertEqual(self.audio.sample_rate, 8000)
        self.assertEqual(self.audio.compression, 'mp3')
    
    def test_recording_directory_created(self):
        """Test recording directory is created"""
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertTrue(os.path.isdir(self.temp_dir))
    
    def test_cleanup_old_files(self):
        """Test cleanup of old files"""
        # Create a test file
        test_file = Path(self.temp_dir) / 'test.mp3'
        test_file.touch()
        
        # Modify time to be old (25 hours ago)
        import time
        old_time = time.time() - (25 * 3600)
        os.utime(test_file, (old_time, old_time))
        
        # Run cleanup
        self.audio.cleanup_old_files(max_age_hours=24)
        
        # File should be deleted
        self.assertFalse(test_file.exists())


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("EasyDispatch Collector - Unit Tests")
    print("=" * 60)
    print()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDisplayManager))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAPIClient))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAudioCapture))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
