# Live Audio Streaming - Quick Start Guide

This guide will help you get the live audio streaming feature up and running.

## Overview

The EasyDispatch audio streaming system allows you to monitor DMR transmissions in real-time through a web browser. Audio is captured from both DMR timeslots, encoded to Opus format, and streamed to your browser with low latency (500ms - 1.5s).

## Prerequisites

### Raspberry Pi
- FFmpeg with Opus codec support
- Working MMDVM installation
- Network connectivity to backend server

### Backend Server
- PHP 7.4+ with write permissions to `backend/tmp/audio_buffers/`
- Web server (Apache/Nginx) configured for SSE

## Installation Steps

### 1. Install FFmpeg on Raspberry Pi

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

Verify Opus support:
```bash
ffmpeg -codecs | grep opus
```

You should see:
```
DEA.L. opus            Opus (Opus Interactive Audio Codec)
```

### 2. Enable Audio Streaming

Edit `/etc/easydispatch/config.yaml`:

```yaml
audio_streaming:
  enabled: true              # Set to true
  capture_device: "plughw:0,0"
  sample_rate: 8000
  bitrate: 16               # kbps per slot
  chunk_duration_ms: 100    # Lower = less latency
  max_retries: 5
  retry_delay: 2
```

### 3. Restart Collector

```bash
sudo systemctl restart easydispatch-collector
```

### 4. Verify Streaming

Check logs:
```bash
sudo journalctl -u easydispatch-collector -f | grep -i "audio"
```

You should see:
```
Audio streaming is enabled
Initialized Audio Streamer
```

### 5. Access Live Dashboard

Open in your browser:
```
https://your-server.com/public/dashboard/live-audio.html
```

Click "Connect" for Slot 1 and/or Slot 2.

## Usage

### Browser Interface

1. **Connect**: Click "Connect" button for each slot you want to monitor
2. **Monitor**: View real-time transmission info (Radio ID, TalkGroup, Duration)
3. **Waveform**: Visual representation of audio activity
4. **Metrics**: Latency, packet count, and bitrate display
5. **Mute**: Toggle audio on/off without disconnecting
6. **Disconnect**: Stop streaming

### What You'll See

When a transmission occurs:
- Status badge turns green "Active"
- Radio ID and TalkGroup are displayed
- Waveform animates
- Duration counter updates
- Audio plays (if not muted)

### Troubleshooting

#### No Audio
1. Check FFmpeg is installed: `ffmpeg -version`
2. Check ALSA device: `arecord -l`
3. Check collector logs: `sudo journalctl -u easydispatch-collector -f`
4. Verify audio_streaming enabled in config

#### High Latency
- Reduce `chunk_duration_ms` (minimum 20ms)
- Check network latency: `ping your-server.com`
- Ensure server has adequate resources

#### Connection Errors
- Check API endpoint is accessible: `curl https://your-server.com/api/v1/stream-listen.php?slot=1`
- Verify API key is valid
- Check PHP error logs
- Ensure proper permissions on `backend/tmp/audio_buffers/`

#### Choppy Audio
- Increase `chunk_duration_ms` (up to 200ms)
- Check CPU usage on Raspberry Pi: `htop`
- Verify network stability
- Check FFmpeg is not being throttled

## Performance Tuning

### Low Latency (500ms-1s)
```yaml
chunk_duration_ms: 50
bitrate: 16
```
- Pros: Ultra-low latency
- Cons: Higher CPU, more network packets

### Balanced (1s-1.5s)
```yaml
chunk_duration_ms: 100
bitrate: 16
```
- Pros: Good balance
- Cons: Moderate latency

### Stable Connection (1.5s-2s)
```yaml
chunk_duration_ms: 200
bitrate: 12
```
- Pros: More stable, lower bandwidth
- Cons: Higher latency

## Architecture

```
MMDVM Hardware (Dual-Slot) 
    ↓ ALSA
FFmpeg (Opus Encoder)
    ↓ 16kbps/slot
Python Collector (audio_streamer.py)
    ↓ HTTP POST (base64)
PHP Backend (stream-audio.php)
    ↓ File Buffer
PHP SSE Server (stream-listen.php)
    ↓ Server-Sent Events
Browser (EventSource + Web Audio API)
    ↓ Audio Playback
Speakers 🔊
```

## Bandwidth Usage

- Slot 1: 16 kbps
- Slot 2: 16 kbps
- HTTP overhead: ~8 kbps
- **Total**: ~40 kbps

This is very efficient and suitable even for mobile connections.

## Security Notes

1. Always use HTTPS in production
2. Keep API keys secure
3. Implement rate limiting (already included)
4. Monitor for abuse
5. Set appropriate CORS headers if needed

## Advanced Configuration

### Custom Audio Device

If you have multiple audio devices:

```bash
# List devices
arecord -l

# Use specific device
capture_device: "plughw:1,0"  # Card 1, Device 0
```

### Multiple Listeners

The system supports multiple concurrent browser connections to the same slot. Each client receives an independent SSE stream.

### Recording While Streaming

Streaming and recording work simultaneously. Enable both:

```yaml
audio:
  compression: "opus"  # Match streaming codec
audio_streaming:
  enabled: true
```

## API Integration

### Send Audio Chunk (Raspberry Pi)

```python
import base64
import requests

# Encode chunk
with open('chunk.opus', 'rb') as f:
    chunk_data = base64.b64encode(f.read()).decode()

# Send to API
response = requests.post(
    'https://your-server.com/api/v1/stream-audio.php',
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    json={
        'slot': 1,
        'radio_id': 2222001,
        'talkgroup_id': 1,
        'chunk_data': chunk_data,
        'sequence': 0
    }
)
```

### Listen to Stream (JavaScript)

```javascript
const eventSource = new EventSource('/api/v1/stream-listen.php?slot=1');

eventSource.addEventListener('audio_chunk', (e) => {
    const data = JSON.parse(e.data);
    console.log('Chunk', data.sequence, 'size:', data.size);
    // Decode and play audio...
});
```

## Support

For detailed documentation, see:
- [AUDIO_STREAMING.md](AUDIO_STREAMING.md) - Complete technical documentation
- [API_REFERENCE.md](API_REFERENCE.md) - API endpoint details
- [README.md](../../README.md) - General system documentation

For issues:
- GitHub Issues: https://github.com/cris-deitos/EasyDispatch/issues

## License

MIT License - See LICENSE file
