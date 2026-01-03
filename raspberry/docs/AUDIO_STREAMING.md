# Audio Streaming Documentation

## Overview

EasyDispatch implements a complete real-time audio streaming system for dual-slot DMR reception. The system streams live audio from both timeslots simultaneously with ultra-low latency (500ms - 1.5s).

> **Note on Dual-Slot Audio**: The current implementation captures audio from a single ALSA device. For true independent dual-slot streaming, MMDVM needs to be configured to output separate audio streams per timeslot, or use DMR-specific audio routing. In most standard MMDVM configurations, both slots share the same audio output path. This is suitable for monitoring but for full dual-slot independent audio, hardware/firmware modifications may be required.

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   MMDVM     │───▶│   FFmpeg     │───▶│   Python    │───▶│     PHP      │
│  Hardware   │    │ Opus Encode  │    │  Collector  │    │   Backend    │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                                                    │
                                                                    ▼
                                                           ┌──────────────┐
                                                           │  File Buffer │
                                                           └──────────────┘
                                                                    │
                                                                    ▼
                                                           ┌──────────────┐
                                                           │  SSE Stream  │
                                                           └──────────────┘
                                                                    │
                                                                    ▼
                                                           ┌──────────────┐
                                                           │   Browser    │
                                                           │ (Web Audio)  │
                                                           └──────────────┘
```

## Components

### 1. Raspberry Pi - Audio Streamer

**File**: `raspberry/easydispatch-collector/collector/audio_streamer.py`

#### Features
- Dual-slot simultaneous streaming
- Opus codec for efficient bandwidth usage (16kbps per slot)
- 100ms chunk duration for low latency
- Automatic reconnection on failure
- Independent stream management per slot

#### Configuration

```yaml
audio_streaming:
  enabled: true
  capture_device: "plughw:0,0"
  sample_rate: 8000
  bitrate: 16  # kbps per slot
  chunk_duration_ms: 100
  max_retries: 5
  retry_delay: 2
```

#### How It Works

1. **Capture**: Uses ALSA to capture audio from MMDVM hardware
2. **Encode**: FFmpeg encodes to Opus in real-time
3. **Chunk**: Splits stream into 100ms chunks
4. **Encode Base64**: Encodes binary chunks to base64 for HTTP transport
5. **Send**: HTTP POST to PHP backend endpoint
6. **Retry**: Automatic retry on network failures

#### Usage

```python
from collector.audio_streamer import AudioStreamer

# Initialize
streamer = AudioStreamer(config, api_client)

# Start streaming slot 1
streamer.start_stream(slot=1, radio_id=2222001, talkgroup_id=1)

# Stop streaming
streamer.stop_stream(slot=1)

# Check if streaming
if streamer.is_streaming(1):
    info = streamer.get_stream_info(1)
    print(f"Streaming {info['chunk_count']} chunks")
```

### 2. Backend - Stream Reception

**File**: `backend/api/v1/stream-audio.php`

#### Features
- Receives and validates audio chunks
- Rate limiting (1000 requests/minute)
- File-based circular buffer (last 50 chunks)
- Metadata tracking per slot
- Optional permanent recording

#### Buffer Structure

```
backend/tmp/audio_buffers/
├── slot1/
│   ├── r2222001_tg1_20260103131500_0.opus
│   ├── r2222001_tg1_20260103131500_1.opus
│   ├── r2222001_tg1_20260103131500_2.opus
│   └── current_meta.json
└── slot2/
    ├── r2222002_tg9_20260103131505_0.opus
    ├── r2222002_tg9_20260103131505_1.opus
    └── current_meta.json
```

#### Metadata Format

```json
{
  "transmission_id": "r2222001_tg1_20260103131500",
  "slot": 1,
  "radio_id": 2222001,
  "talkgroup_id": 1,
  "last_sequence": 25,
  "last_update": 1704285900,
  "timestamp": "2026-01-03T13:15:00"
}
```

#### API Request

```bash
curl -X POST https://your-server.com/api/v1/stream-audio.php \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "slot": 1,
    "radio_id": 2222001,
    "talkgroup_id": 1,
    "chunk_data": "base64_encoded_opus_data_here",
    "sequence": 0,
    "timestamp": "2026-01-03T13:15:00"
  }'
```

### 3. Backend - Stream Distribution

**File**: `backend/api/v1/stream-listen.php`

#### Features
- Server-Sent Events (SSE) protocol
- Per-slot streaming
- Keep-alive every 15 seconds
- Auto-timeout after 5 minutes
- Transmission start/end detection

#### SSE Events

##### Connected
```
event: connected
data: {"slot": 1, "message": "Connected to slot 1"}
```

##### Transmission Start
```
event: transmission_start
data: {
  "transmission_id": "r2222001_tg1_20260103131500",
  "slot": 1,
  "radio_id": 2222001,
  "talkgroup_id": 1,
  "timestamp": "2026-01-03T13:15:00"
}
```

##### Audio Chunk
```
event: audio_chunk
data: {
  "sequence": 5,
  "chunk": "base64_encoded_opus_data",
  "size": 200
}
```

##### Transmission End
```
event: transmission_end
data: {"transmission_id": "r2222001_tg1_20260103131500"}
```

##### Keep-Alive
```
event: keepalive
data: {"timestamp": 1704285900}
```

### 4. Frontend - Live Audio Player

**File**: `backend/public/dashboard/live-audio.html`

#### Features
- Dual-slot independent players
- Real-time waveform visualization
- EventSource (SSE) client
- Web Audio API for playback
- Latency monitoring
- Packet counter
- Bitrate display
- Auto-reconnection

#### Usage

1. Open in browser: `https://your-server.com/public/dashboard/live-audio.html`
2. Click "Connect" for Slot 1 and/or Slot 2
3. Audio streams automatically when transmissions occur
4. View real-time metrics and waveforms

#### Browser Requirements

- Modern browser with EventSource support (Chrome, Firefox, Safari, Edge)
- Web Audio API support
- JavaScript enabled

## Technical Specifications

### Audio Format
- **Codec**: Opus
- **Bitrate**: 16 kbps per slot
- **Sample Rate**: 8 kHz
- **Channels**: Mono
- **Frame Duration**: 100ms
- **Application**: VoIP mode

### Latency Components
- FFmpeg encoding: ~50-100ms
- Network transmission: ~100-300ms
- PHP processing: ~10-50ms
- SSE polling: ~50ms
- Browser decode/play: ~200-500ms
- **Total**: 500ms - 1.5s

### Bandwidth Usage
- Per slot: 16 kbps
- Dual-slot: 32 kbps
- With overhead: ~40 kbps total

### Buffer Management
- Circular buffer: 50 chunks (5 seconds)
- Automatic cleanup of old chunks
- Metadata update every chunk
- Stale detection: 5 seconds

## Configuration

### Raspberry Pi

Edit `/etc/easydispatch/config.yaml`:

```yaml
audio_streaming:
  enabled: true
  capture_device: "plughw:0,0"
  sample_rate: 8000
  bitrate: 16
  chunk_duration_ms: 100
  max_retries: 5
  retry_delay: 2
```

### PHP Backend

No special configuration needed. Ensure:
- Write permissions on `backend/tmp/audio_buffers/`
- PHP `max_execution_time` = 0 or high value for SSE
- `output_buffering` = Off for SSE

### Web Server

#### Apache

Add to your VirtualHost:

```apache
<Location /api/v1/stream-listen.php>
    # Disable buffering for SSE
    SetEnv no-gzip 1
</Location>
```

#### Nginx

```nginx
location /api/v1/stream-listen.php {
    # Disable buffering for SSE
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 600s;
}
```

## Troubleshooting

### No Audio Received

1. Check FFmpeg installation:
   ```bash
   ffmpeg -version | grep opus
   ```

2. Check ALSA device:
   ```bash
   arecord -l
   arecord -D plughw:0,0 -d 5 test.wav
   ```

3. Check Python logs:
   ```bash
   sudo journalctl -u easydispatch-collector -f | grep audio_streamer
   ```

### High Latency

- Reduce `chunk_duration_ms` (minimum 20ms)
- Check network latency: `ping your-server.com`
- Reduce PHP buffer cleanup frequency
- Use faster hosting/VPS

### Choppy Audio

- Increase `chunk_duration_ms` (up to 200ms)
- Check CPU usage: `htop`
- Verify FFmpeg settings
- Check network stability

### Browser Not Receiving Stream

1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify SSE connection:
   ```javascript
   // In console
   console.log(slots[1].eventSource.readyState);
   // Should be 1 (OPEN)
   ```

4. Check network tab for SSE events

### Buffer Directory Issues

```bash
# Create directories
sudo mkdir -p /var/www/easydispatch/backend/tmp/audio_buffers/slot{1,2}

# Set permissions
sudo chown -R www-data:www-data /var/www/easydispatch/backend/tmp
sudo chmod -R 755 /var/www/easydispatch/backend/tmp
```

## Performance Optimization

### CPU Usage
- Opus encoding: ~5-10% per slot on RPi3
- Python overhead: ~5%
- Total: ~15-25% CPU usage

### Memory Usage
- FFmpeg: ~20-30 MB per slot
- Python: ~30-40 MB
- Buffer: ~1-2 MB
- Total: ~80-120 MB

### Network Optimization
- Use compression for HTTP POST
- Batch multiple chunks if latency allows
- Implement adaptive bitrate based on network

## Security Considerations

1. **API Authentication**: Always use API keys
2. **Rate Limiting**: Prevent abuse (1000 req/min)
3. **Input Validation**: Validate all chunk data
4. **HTTPS Only**: Never use HTTP in production
5. **Buffer Cleanup**: Auto-delete old files

## Future Enhancements

- [ ] Adaptive bitrate streaming
- [ ] WebRTC for lower latency
- [ ] Browser-native Opus decoding
- [ ] Multi-receiver aggregation
- [ ] Recording playback controls
- [ ] Mobile app support

## References

- [Opus Codec](https://opus-codec.org/)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
