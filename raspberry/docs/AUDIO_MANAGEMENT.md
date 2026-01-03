# Audio Management Guide

This guide covers audio capture, compression, upload, and automatic cleanup in the EasyDispatch system.

## Overview

The EasyDispatch collector captures audio from DMR transmissions, compresses it to save storage space, uploads it to the backend server, and automatically cleans up local files.

## Audio Flow

```
┌─────────────────┐
│ DMR Transmission│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Audio Capture  │ ← arecord (WAV format)
│  (Raspberry Pi) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MP3 Compression │ ← FFmpeg (64kbps default)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Upload to API  │ ← HTTPS POST
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Auto-Delete     │ ← Remove from Raspberry
│ (if successful) │
└─────────────────┘
```

## Audio Capture Configuration

Edit `/etc/easydispatch/config.yaml`:

```yaml
audio:
  capture_device: "plughw:0,0"      # ALSA audio device
  sample_rate: 8000                  # Sample rate in Hz
  format: "wav"                      # Initial capture format
  compression: "mp3"                 # Compression format (mp3, opus, or wav)
  bitrate: 64                        # Bitrate in kbps for compressed formats
  recording_dir: "/var/lib/easydispatch/audio"  # Local storage directory
```

### Configuration Options

#### capture_device
The ALSA device to capture audio from. Use `arecord -l` to list available devices.

Example output:
```
card 0: Codec [USB Audio Codec], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
```

For this device, use: `plughw:0,0` (card 0, device 0)

#### sample_rate
Sample rate for audio capture. Common values:
- `8000` - Standard for voice (DMR uses 8kHz)
- `16000` - Higher quality
- `48000` - CD quality (not recommended for DMR)

**Recommendation**: Keep at `8000` for DMR.

#### compression
Compression format to use:
- **mp3** - Good compression, widely compatible (recommended)
- **opus** - Better compression, modern codec
- **wav** - No compression, larger files

**Recommendation**: Use `mp3` for best compatibility and space savings.

#### bitrate
Bitrate for compressed audio in kilobits per second (kbps):
- `32` - Very compressed, lower quality
- `64` - Good balance (recommended)
- `128` - Higher quality, larger files

**Recommendation**: `64` kbps is sufficient for DMR voice quality.

## Space Savings

### Compression Comparison

For a typical 10-second DMR transmission:

| Format | Size | Compression Ratio |
|--------|------|-------------------|
| WAV (uncompressed) | ~160 KB | - |
| MP3 64kbps | ~80 KB | 50% reduction |
| MP3 32kbps | ~40 KB | 75% reduction |
| Opus 32kbps | ~35 KB | 78% reduction |

### Storage Requirements

Average transmission: 5 seconds
Average daily transmissions: 500
Average monthly storage (MP3 64kbps): ~10 MB

With auto-cleanup enabled, Raspberry Pi storage usage is minimal as files are deleted immediately after successful upload.

## Automatic Cleanup

### How It Works

The system implements a two-stage cleanup strategy:

#### 1. Immediate Deletion After Upload

When an audio file is successfully uploaded to the backend:
1. API confirms successful upload (HTTP 200 + success flag)
2. File is immediately deleted from Raspberry Pi
3. Logged: `Audio file deleted from Raspberry: /path/to/file.mp3`

This ensures files are only kept for the time needed to transfer them.

#### 2. Periodic Cleanup (Fallback)

A background thread runs every hour (configurable) to clean up:
- Old audio files (24+ hours)
- Failed uploads
- Orphaned temporary files

Configuration:
```yaml
polling:
  cleanup_interval: 3600  # Seconds (1 hour)
```

### Offline Queue Handling

If the API is unreachable:
1. Audio files are queued for later upload
2. Files remain on Raspberry Pi until successfully uploaded
3. Automatic retry with exponential backoff
4. Files are deleted after successful retry upload

### Manual Cleanup

To manually clean up old audio files:

```bash
# Delete files older than 24 hours
sudo find /var/lib/easydispatch/audio -type f -mtime +1 -delete

# Delete all audio files
sudo rm -f /var/lib/easydispatch/audio/*
```

## Audio Upload Process

### Upload Flow

1. **Capture**: Audio captured as WAV
2. **Compress**: Converted to MP3 (or configured format)
3. **POST**: Uploaded via HTTPS to `/api/v1/transmissions`
4. **Verify**: Check for success response
5. **Delete**: Remove file from Raspberry Pi if successful
6. **Queue**: If failed, add to offline queue for retry

### Upload Endpoint

The audio is uploaded to:
```
POST /api/v1/transmissions
```

With multipart form data:
```
audio: <file>
radio_id: 2222000
talkgroup_id: 1
timeslot: 1
start_time: 2024-01-01 12:00:00
end_time: 2024-01-01 12:00:05
duration: 5
rssi: -75
ber: 0.5
```

### Backend Storage

On the backend server, audio files are stored in:
```
/path/to/easydispatch/backend/audio/
```

Filename format:
```
YYYYMMDD_HHMMSS_<radio_id>_slot<N>_<unique_id>.mp3
```

Example:
```
20240103_153045_2222000_slot1_abc123def.mp3
```

## Monitoring

### Check Audio Files on Raspberry Pi

```bash
# List audio files
ls -lh /var/lib/easydispatch/audio/

# Check disk usage
du -sh /var/lib/easydispatch/audio/

# Monitor in real-time
watch -n 5 'ls -lh /var/lib/easydispatch/audio/ | tail -10'
```

### Check Logs

```bash
# View collector logs
sudo journalctl -u easydispatch-collector -f

# Search for audio-related logs
sudo journalctl -u easydispatch-collector | grep -i audio

# Search for deletion logs
sudo journalctl -u easydispatch-collector | grep -i "deleted"
```

### Expected Log Messages

**Successful Flow:**
```
Audio recording started: slot1_2222000_tg1_20240103_153045.wav
Recording saved: /var/lib/easydispatch/audio/slot1_2222000_tg1_20240103_153045.wav (160000 bytes)
Compressing audio to mp3...
Compression complete: 80000 bytes (50.0% reduction)
Transmission posted successfully: 12345
Audio file deleted from Raspberry: /var/lib/easydispatch/audio/slot1_2222000_tg1_20240103_153045.mp3
```

**Failed Upload (Queued):**
```
Audio recording started: slot1_2222000_tg1_20240103_153045.wav
Recording saved: /var/lib/easydispatch/audio/slot1_2222000_tg1_20240103_153045.wav (160000 bytes)
Compressing audio to mp3...
Compression complete: 80000 bytes (50.0% reduction)
API request failed: Connection error
Queued transmission for retry (queue size: 5)
```

**Successful Retry:**
```
Queued transmission posted successfully
Audio file deleted from Raspberry: /var/lib/easydispatch/audio/slot1_2222000_tg1_20240103_153045.mp3
```

## Troubleshooting

### Audio Files Not Being Deleted

1. **Check API connectivity**:
   ```bash
   curl -I https://your-server.com/api/v1/radios
   ```

2. **Check collector logs**:
   ```bash
   sudo journalctl -u easydispatch-collector | grep -i "transmission posted"
   ```

3. **Verify API key**:
   ```bash
   sudo grep "key:" /etc/easydispatch/config.yaml
   ```

4. **Check permissions**:
   ```bash
   ls -la /var/lib/easydispatch/audio/
   ```

### Audio Files Accumulating

If audio files are accumulating despite successful uploads:

1. **Check for errors in logs**:
   ```bash
   sudo journalctl -u easydispatch-collector | grep -i error
   ```

2. **Verify disk space**:
   ```bash
   df -h
   ```

3. **Manually trigger cleanup**:
   ```bash
   sudo systemctl restart easydispatch-collector
   ```

4. **Check offline queue**:
   ```bash
   cat /var/lib/easydispatch/offline_queue.json | jq .
   ```

### Compression Failures

If FFmpeg compression is failing:

1. **Check FFmpeg installation**:
   ```bash
   ffmpeg -version
   ```

2. **Test MP3 encoding**:
   ```bash
   ffmpeg -i test.wav -codec:a libmp3lame -b:a 64k test.mp3
   ```

3. **Check logs**:
   ```bash
   sudo journalctl -u easydispatch-collector | grep -i compress
   ```

### Large Audio Files

If audio files are larger than expected:

1. **Verify compression is enabled**:
   ```bash
   sudo grep "compression:" /etc/easydispatch/config.yaml
   ```

2. **Check bitrate setting**:
   ```bash
   sudo grep "bitrate:" /etc/easydispatch/config.yaml
   ```

3. **Test manual compression**:
   ```bash
   ffmpeg -i /var/lib/easydispatch/audio/test.wav -codec:a libmp3lame -b:a 64k test.mp3
   ls -lh test.mp3
   ```

## Best Practices

1. **Monitor Disk Space**: Set up alerts for low disk space
   ```bash
   # Add to crontab
   0 * * * * /usr/local/bin/check-disk-space.sh
   ```

2. **Regular Log Review**: Check logs weekly for upload failures
   ```bash
   sudo journalctl -u easydispatch-collector --since "1 week ago" | grep -i "failed"
   ```

3. **Backup Configuration**: Keep a backup of your configuration
   ```bash
   sudo cp /etc/easydispatch/config.yaml /etc/easydispatch/config.yaml.backup
   ```

4. **Test Recovery**: Periodically test the offline queue recovery
   - Disconnect network
   - Generate some transmissions
   - Reconnect network
   - Verify files are uploaded and deleted

## Performance Impact

### CPU Usage
- Audio capture: ~1-2% CPU
- MP3 compression: ~5-10% CPU per file (brief spike)
- Upload: ~1-2% CPU

### Memory Usage
- Audio buffers: ~2 MB per active transmission
- Compression: ~5 MB temporary

### Network Usage
- Per transmission (5 seconds, MP3 64kbps): ~40 KB
- 500 transmissions/day: ~20 MB/day
- Monthly (estimated): ~600 MB

## Security Considerations

1. **File Permissions**: Audio files are created with restrictive permissions
   ```bash
   sudo chmod 755 /var/lib/easydispatch/audio
   ```

2. **Secure Transfer**: All uploads use HTTPS
3. **API Authentication**: Bearer token authentication required
4. **Automatic Cleanup**: Reduces exposure window for sensitive audio

## References

- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [ALSA Documentation](https://www.alsa-project.org/wiki/Main_Page)
- [EasyDispatch API Reference](API_REFERENCE.md)
