"""
Audio Streamer Module
Real-time audio streaming with Opus encoding for dual-slot DMR
Streams audio chunks to PHP backend via HTTP POST
"""

import os
import subprocess
import logging
import threading
import time
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import queue

logger = logging.getLogger(__name__)


class AudioStreamer:
    """Stream audio in real-time using Opus codec"""
    
    def __init__(self, config: dict, api_client):
        """
        Initialize Audio Streamer
        
        Args:
            config: Audio streaming configuration dictionary
            api_client: API client for sending chunks
        """
        self.capture_device = config.get('capture_device', 'plughw:0,0')
        self.sample_rate = config.get('sample_rate', 8000)
        self.bitrate = config.get('bitrate', 16)  # kbps per slot
        self.chunk_duration_ms = config.get('chunk_duration_ms', 100)
        self.api_client = api_client
        
        # Active streams for each slot
        self.active_streams = {}
        self.stream_threads = {}
        self.stream_queues = {}
        
        # Reconnection settings
        self.max_retries = config.get('max_retries', 5)
        self.retry_delay = config.get('retry_delay', 2)
        
        logger.info(f"Initialized Audio Streamer (device: {self.capture_device}, "
                   f"rate: {self.sample_rate}, bitrate: {self.bitrate}kbps)")
    
    def start_stream(self, slot: int, radio_id: int, talkgroup_id: int) -> bool:
        """
        Start streaming audio for a slot
        
        Args:
            slot: DMR slot number (1 or 2)
            radio_id: DMR radio ID
            talkgroup_id: Talkgroup ID
            
        Returns:
            True if stream started successfully
        """
        if slot in self.active_streams:
            logger.warning(f"Stream already active for slot {slot}")
            return False
        
        logger.info(f"Starting audio stream for slot {slot} (Radio: {radio_id}, TG: {talkgroup_id})")
        
        try:
            # Create queue for this stream
            self.stream_queues[slot] = queue.Queue(maxsize=50)
            
            # Start FFmpeg process for Opus encoding
            process = self._start_ffmpeg_process(slot)
            if not process:
                return False
            
            # Store stream info
            self.active_streams[slot] = {
                'process': process,
                'radio_id': radio_id,
                'talkgroup_id': talkgroup_id,
                'start_time': datetime.now(),
                'chunk_count': 0
            }
            
            # Start streaming thread
            thread = threading.Thread(
                target=self._stream_worker,
                args=(slot,),
                daemon=True
            )
            thread.start()
            self.stream_threads[slot] = thread
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start stream for slot {slot}: {e}", exc_info=True)
            self._cleanup_stream(slot)
            return False
    
    def stop_stream(self, slot: int) -> bool:
        """
        Stop streaming audio for a slot
        
        Args:
            slot: DMR slot number (1 or 2)
            
        Returns:
            True if stream stopped successfully
        """
        if slot not in self.active_streams:
            logger.warning(f"No active stream for slot {slot}")
            return False
        
        logger.info(f"Stopping audio stream for slot {slot}")
        
        try:
            # Signal thread to stop by closing queue
            if slot in self.stream_queues:
                self.stream_queues[slot].put(None)
            
            # Wait for thread to finish
            if slot in self.stream_threads:
                self.stream_threads[slot].join(timeout=5)
            
            # Cleanup
            self._cleanup_stream(slot)
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping stream for slot {slot}: {e}", exc_info=True)
            return False
    
    def _start_ffmpeg_process(self, slot: int) -> Optional[subprocess.Popen]:
        """
        Start FFmpeg process for Opus encoding
        
        Args:
            slot: DMR slot number
            
        Returns:
            Process object or None if failed
        """
        try:
            cmd = [
                'ffmpeg',
                '-f', 'alsa',
                '-i', self.capture_device,
                '-acodec', 'libopus',
                '-b:a', f'{self.bitrate}k',
                '-ar', str(self.sample_rate),
                '-ac', '1',  # Mono
                '-application', 'voip',
                '-frame_duration', str(self.chunk_duration_ms),
                '-vbr', 'off',  # Constant bitrate
                '-f', 'opus',
                '-'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            logger.info(f"FFmpeg process started for slot {slot}")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start FFmpeg: {e}", exc_info=True)
            return None
    
    def _stream_worker(self, slot: int):
        """
        Worker thread that reads chunks and sends to API
        
        Args:
            slot: DMR slot number
        """
        stream_info = self.active_streams.get(slot)
        if not stream_info:
            return
        
        process = stream_info['process']
        radio_id = stream_info['radio_id']
        talkgroup_id = stream_info['talkgroup_id']
        
        # Calculate chunk size in bytes
        # Opus at 16kbps for 100ms = 16000/8 * 0.1 = 200 bytes (approximate)
        chunk_size = int((self.bitrate * 1000 / 8) * (self.chunk_duration_ms / 1000))
        
        retry_count = 0
        
        while True:
            try:
                # Read chunk from FFmpeg stdout
                chunk = process.stdout.read(chunk_size)
                
                if not chunk:
                    logger.info(f"Stream ended for slot {slot} (no more data)")
                    break
                
                # Encode chunk to base64
                chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                
                # Send to API
                success = self._send_chunk(
                    slot=slot,
                    radio_id=radio_id,
                    talkgroup_id=talkgroup_id,
                    chunk_data=chunk_b64,
                    sequence=stream_info['chunk_count']
                )
                
                if success:
                    stream_info['chunk_count'] += 1
                    retry_count = 0
                else:
                    # Handle retry
                    retry_count += 1
                    if retry_count >= self.max_retries:
                        logger.error(f"Max retries reached for slot {slot}, stopping stream")
                        break
                    time.sleep(self.retry_delay)
                
                # Check if we should stop
                if slot in self.stream_queues:
                    try:
                        stop_signal = self.stream_queues[slot].get_nowait()
                        if stop_signal is None:
                            logger.info(f"Received stop signal for slot {slot}")
                            break
                    except queue.Empty:
                        pass
                
            except Exception as e:
                logger.error(f"Error in stream worker for slot {slot}: {e}", exc_info=True)
                time.sleep(1)
        
        logger.info(f"Stream worker finished for slot {slot} (sent {stream_info['chunk_count']} chunks)")
    
    def _send_chunk(self, slot: int, radio_id: int, talkgroup_id: int, 
                    chunk_data: str, sequence: int) -> bool:
        """
        Send audio chunk to API
        
        Args:
            slot: DMR slot number
            radio_id: Radio ID
            talkgroup_id: TalkGroup ID
            chunk_data: Base64 encoded chunk
            sequence: Chunk sequence number
            
        Returns:
            True if sent successfully
        """
        try:
            payload = {
                'slot': slot,
                'radio_id': radio_id,
                'talkgroup_id': talkgroup_id,
                'chunk_data': chunk_data,
                'sequence': sequence,
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.api_client.post('/stream-audio', payload)
            
            if response and response.get('success'):
                return True
            else:
                logger.warning(f"Failed to send chunk {sequence} for slot {slot}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending chunk: {e}", exc_info=True)
            return False
    
    def _cleanup_stream(self, slot: int):
        """
        Cleanup resources for a stream
        
        Args:
            slot: DMR slot number
        """
        # Terminate FFmpeg process
        if slot in self.active_streams:
            process = self.active_streams[slot]['process']
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                logger.error(f"Error terminating process for slot {slot}: {e}")
            
            del self.active_streams[slot]
        
        # Remove queue
        if slot in self.stream_queues:
            del self.stream_queues[slot]
        
        # Remove thread reference
        if slot in self.stream_threads:
            del self.stream_threads[slot]
    
    def is_streaming(self, slot: int) -> bool:
        """
        Check if a slot is currently streaming
        
        Args:
            slot: DMR slot number
            
        Returns:
            True if streaming
        """
        return slot in self.active_streams
    
    def get_stream_info(self, slot: int) -> Optional[Dict]:
        """
        Get information about active stream
        
        Args:
            slot: DMR slot number
            
        Returns:
            Stream info dict or None
        """
        if slot not in self.active_streams:
            return None
        
        info = self.active_streams[slot].copy()
        info.pop('process', None)  # Don't include process object
        return info
    
    def cleanup_all(self):
        """Stop all active streams and cleanup"""
        logger.info("Cleaning up all audio streams...")
        
        slots = list(self.active_streams.keys())
        for slot in slots:
            self.stop_stream(slot)
        
        logger.info("Audio streamer cleanup complete")
