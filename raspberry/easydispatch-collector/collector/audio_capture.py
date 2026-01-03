"""
Audio Capture Module
Captures and processes audio from DMR transmissions
"""

import os
import subprocess
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class AudioCapture:
    """Capture and encode audio from DMR transmissions"""
    
    def __init__(self, config: dict):
        """
        Initialize Audio Capture
        
        Args:
            config: Audio configuration dictionary
        """
        self.capture_device = config.get('capture_device', 'plughw:0,0')
        self.sample_rate = config.get('sample_rate', 8000)
        self.format = config.get('format', 'wav')
        self.compression = config.get('compression', 'mp3')
        self.bitrate = config.get('bitrate', 64)
        self.recording_dir = Path(config.get('recording_dir', '/tmp/easydispatch/audio'))
        
        # Create recording directory
        self.recording_dir.mkdir(parents=True, exist_ok=True)
        
        self.active_recordings = {}
        
        logger.info(f"Initialized Audio Capture (device: {self.capture_device}, rate: {self.sample_rate})")
    
    def start_recording(self, slot: int, radio_id: int, talkgroup_id: int) -> str:
        """
        Start recording audio for a transmission
        
        Args:
            slot: DMR slot number (1 or 2)
            radio_id: DMR radio ID
            talkgroup_id: Talkgroup ID
            
        Returns:
            Recording ID (file path)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"slot{slot}_{radio_id}_tg{talkgroup_id}_{timestamp}.wav"
        filepath = self.recording_dir / filename
        
        logger.info(f"Starting audio recording: {filename}")
        
        try:
            # Start arecord process
            cmd = [
                'arecord',
                '-D', self.capture_device,
                '-f', 'S16_LE',
                '-r', str(self.sample_rate),
                '-c', '1',  # Mono
                str(filepath)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            recording_id = f"slot{slot}_{radio_id}_{timestamp}"
            self.active_recordings[recording_id] = {
                'process': process,
                'filepath': filepath,
                'slot': slot,
                'radio_id': radio_id,
                'talkgroup_id': talkgroup_id,
                'start_time': datetime.now()
            }
            
            return recording_id
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}", exc_info=True)
            return None
    
    def stop_recording(self, recording_id: str) -> Optional[Path]:
        """
        Stop an active recording
        
        Args:
            recording_id: Recording ID returned by start_recording
            
        Returns:
            Path to recorded file, or None if failed
        """
        if recording_id not in self.active_recordings:
            logger.warning(f"Recording ID not found: {recording_id}")
            return None
        
        recording = self.active_recordings[recording_id]
        process = recording['process']
        filepath = recording['filepath']
        
        logger.info(f"Stopping audio recording: {recording_id}")
        
        try:
            # Terminate arecord process
            process.terminate()
            process.wait(timeout=5)
            
            # Check if file was created
            if filepath.exists() and filepath.stat().st_size > 0:
                logger.info(f"Recording saved: {filepath} ({filepath.stat().st_size} bytes)")
                
                # Compress if needed
                if self.compression and self.compression != 'wav':
                    compressed_path = self._compress_audio(filepath)
                    if compressed_path:
                        # Remove original WAV file
                        filepath.unlink()
                        filepath = compressed_path
                
                del self.active_recordings[recording_id]
                return filepath
            else:
                logger.warning(f"Recording file is empty or not created: {filepath}")
                if filepath.exists():
                    filepath.unlink()
                del self.active_recordings[recording_id]
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Failed to stop recording process (timeout)")
            process.kill()
            del self.active_recordings[recording_id]
            return None
        except Exception as e:
            logger.error(f"Error stopping recording: {e}", exc_info=True)
            del self.active_recordings[recording_id]
            return None
    
    def _compress_audio(self, wav_path: Path) -> Optional[Path]:
        """
        Compress WAV file to specified format
        
        Args:
            wav_path: Path to WAV file
            
        Returns:
            Path to compressed file, or None if failed
        """
        if self.compression == 'mp3':
            output_path = wav_path.with_suffix('.mp3')
            
            cmd = [
                'ffmpeg',
                '-i', str(wav_path),
                '-codec:a', 'libmp3lame',
                '-b:a', f'{self.bitrate}k',
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                str(output_path)
            ]
        elif self.compression == 'opus':
            output_path = wav_path.with_suffix('.opus')
            
            cmd = [
                'ffmpeg',
                '-i', str(wav_path),
                '-codec:a', 'libopus',
                '-b:a', f'{self.bitrate}k',
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                str(output_path)
            ]
        else:
            logger.warning(f"Unsupported compression format: {self.compression}")
            return wav_path
        
        try:
            logger.info(f"Compressing audio to {self.compression}...")
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            
            if result.returncode == 0 and output_path.exists():
                original_size = wav_path.stat().st_size
                compressed_size = output_path.stat().st_size
                ratio = (1 - compressed_size / original_size) * 100
                logger.info(f"Compression complete: {compressed_size} bytes ({ratio:.1f}% reduction)")
                return output_path
            else:
                logger.error(f"Compression failed: {result.stderr.decode()}")
                return wav_path
                
        except subprocess.TimeoutExpired:
            logger.error("Compression timeout")
            return wav_path
        except Exception as e:
            logger.error(f"Compression error: {e}", exc_info=True)
            return wav_path
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old recording files
        
        Args:
            max_age_hours: Maximum age in hours before deletion
        """
        import time
        
        cutoff_time = time.time() - (max_age_hours * 3600)
        deleted_count = 0
        
        for filepath in self.recording_dir.glob('*'):
            if filepath.is_file() and filepath.stat().st_mtime < cutoff_time:
                try:
                    filepath.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete {filepath}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old recording files")
