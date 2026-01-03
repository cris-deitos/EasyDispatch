# API Reference - Audio Streaming Endpoints

This document describes the audio streaming API endpoints added to EasyDispatch.

## Authentication

All API endpoints require authentication via API key in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY_HERE
```

## Base URL

```
https://your-hosting.com/easydispatch/api/v1
```

---

## POST /stream-audio

Receives real-time audio chunks from Raspberry Pi collector.

### Request

**Method**: `POST`

**Headers**:
- `Authorization: Bearer {api_key}`
- `Content-Type: application/json`

**Body**:
```json
{
  "slot": 1,
  "radio_id": 2222001,
  "talkgroup_id": 1,
  "chunk_data": "T2dnUwACAAAAAAAAAAD...",
  "sequence": 0,
  "timestamp": "2026-01-03T13:15:00",
  "save_recording": false
}
```

**Parameters**:
- `slot` (integer, required): DMR timeslot (1 or 2)
- `radio_id` (integer, required): DMR radio ID transmitting
- `talkgroup_id` (integer, required): TalkGroup ID
- `chunk_data` (string, required): Base64-encoded Opus audio chunk
- `sequence` (integer, required): Chunk sequence number (starts at 0)
- `timestamp` (string, optional): ISO 8601 timestamp
- `save_recording` (boolean, optional): Save to permanent storage (default: false)

### Response

**Success (200)**:
```json
{
  "success": true,
  "data": {
    "received": true,
    "slot": 1,
    "sequence": 0,
    "size": 200
  }
}
```

**Error (400)**:
```json
{
  "success": false,
  "error": "Missing required field: chunk_data"
}
```

**Error (401)**:
```json
{
  "success": false,
  "error": "Invalid API key"
}
```

**Error (429)**:
```json
{
  "success": false,
  "error": "Rate limit exceeded"
}
```

### Rate Limiting
- 1000 requests per minute per IP

### Notes
- Chunks are stored in a circular buffer (last 50 chunks)
- Old chunks are automatically cleaned up
- Metadata is updated with each chunk
- Transmission is detected as ended after 5 seconds of inactivity

---

## GET /stream-listen

Server-Sent Events (SSE) endpoint for browser clients to receive live audio stream.

### Request

**Method**: `GET`

**Query Parameters**:
- `slot` (integer, required): DMR timeslot to listen to (1 or 2)

**Example**:
```
GET /api/v1/stream-listen.php?slot=1
```

### Response

**Content-Type**: `text/event-stream`

**Connection**: Keep-alive

### SSE Events

#### connected
Sent when client successfully connects.

```
event: connected
data: {"slot": 1, "message": "Connected to slot 1"}
```

#### transmission_start
Sent when a new transmission begins.

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

#### audio_chunk
Sent for each audio chunk during active transmission.

```
event: audio_chunk
data: {
  "sequence": 5,
  "chunk": "T2dnUwACAAAAAAAAAAD...",
  "size": 200
}
```

**Fields**:
- `sequence`: Chunk sequence number
- `chunk`: Base64-encoded Opus audio data
- `size`: Size of decoded audio in bytes

#### transmission_end
Sent when transmission ends (5 seconds of inactivity).

```
event: transmission_end
data: {"transmission_id": "r2222001_tg1_20260103131500"}
```

#### keepalive
Sent every 15 seconds to keep connection alive.

```
event: keepalive
data: {"timestamp": 1704285900}
```

#### timeout
Sent when connection reaches timeout (5 minutes).

```
event: timeout
data: {"message": "Connection timeout"}
```

#### error
Sent when an error occurs.

```
event: error
data: {"error": "Invalid slot"}
```

### Client Example (JavaScript)

```javascript
// Connect to stream
const eventSource = new EventSource('/api/v1/stream-listen.php?slot=1');

// Handle connection
eventSource.addEventListener('connected', (e) => {
  const data = JSON.parse(e.data);
  console.log('Connected to', data.slot);
});

// Handle transmission start
eventSource.addEventListener('transmission_start', (e) => {
  const data = JSON.parse(e.data);
  console.log('Transmission started:', data.radio_id, 'TG:', data.talkgroup_id);
});

// Handle audio chunks
eventSource.addEventListener('audio_chunk', (e) => {
  const data = JSON.parse(e.data);
  console.log('Received chunk', data.sequence, 'size:', data.size);
  
  // Decode base64
  const audioData = atob(data.chunk);
  
  // Play audio (requires Opus decoder)
  // ... decode and play logic here ...
});

// Handle transmission end
eventSource.addEventListener('transmission_end', (e) => {
  console.log('Transmission ended');
});

// Handle errors
eventSource.onerror = (e) => {
  console.error('SSE error:', e);
  eventSource.close();
};

// Close connection
// eventSource.close();
```

### Notes
- SSE is a unidirectional protocol (server to client only)
- Automatic reconnection is handled by browser EventSource API
- Timeout after 5 minutes of connection (refresh to reconnect)
- Compatible with shared hosting (no WebSocket server needed)

---

## Audio Format Specifications

### Codec
- **Format**: Opus
- **Bitrate**: 16 kbps per slot
- **Sample Rate**: 8 kHz
- **Channels**: Mono
- **Frame Duration**: 100ms
- **Application**: VoIP

### Chunk Size
- Approximate size: 200 bytes per 100ms chunk
- Base64 encoded: ~267 characters

### Buffer Management
- Circular buffer: Last 50 chunks (5 seconds)
- Automatic cleanup of old chunks
- Stale detection: 5 seconds without updates

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid API key |
| 405 | Method Not Allowed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Testing

### Test stream-audio endpoint

```bash
# Generate test audio chunk (requires FFmpeg)
ffmpeg -f lavfi -i "sine=frequency=1000:duration=0.1" \
  -acodec libopus -b:a 16k -ar 8000 -ac 1 test.opus

# Encode to base64
CHUNK_DATA=$(base64 -w 0 test.opus)

# Send to API
curl -X POST "https://your-hosting.com/api/v1/stream-audio.php" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"slot\": 1,
    \"radio_id\": 2222001,
    \"talkgroup_id\": 1,
    \"chunk_data\": \"$CHUNK_DATA\",
    \"sequence\": 0
  }"
```

### Test stream-listen endpoint

```bash
# Simple curl test
curl -N "https://your-hosting.com/api/v1/stream-listen.php?slot=1"

# You should see SSE events stream
```

---

## Browser Compatibility

### EventSource (SSE) Support
- ✅ Chrome 6+
- ✅ Firefox 6+
- ✅ Safari 5+
- ✅ Edge 79+
- ✅ Opera 11+
- ❌ Internet Explorer (not supported)

### Web Audio API Support
- ✅ Chrome 10+
- ✅ Firefox 25+
- ✅ Safari 6+
- ✅ Edge 12+
- ✅ Opera 15+

---

## Performance

### Latency
- FFmpeg encoding: 50-100ms
- Network transmission: 100-300ms
- PHP processing: 10-50ms
- SSE polling: ~50ms
- Browser decode/play: 200-500ms
- **Total**: 500ms - 1.5s

### Bandwidth
- Per slot: 16 kbps
- Dual-slot: 32 kbps
- With HTTP overhead: ~40 kbps total

### Scalability
- Shared hosting compatible
- File-based buffering (no database)
- Stateless design
- Multiple concurrent listeners supported

---

## Security

### Best Practices
1. Always use HTTPS in production
2. Keep API keys secure
3. Implement rate limiting
4. Validate all input data
5. Set appropriate CORS headers
6. Monitor for abuse

### CORS Configuration

If accessing from different domain, add CORS headers:

```php
header('Access-Control-Allow-Origin: https://your-dashboard-domain.com');
header('Access-Control-Allow-Methods: GET, POST');
header('Access-Control-Allow-Headers: Authorization, Content-Type');
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/cris-deitos/EasyDispatch/issues
- Documentation: https://github.com/cris-deitos/EasyDispatch

---

## Changelog

### v1.0.0 (2026-01-03)
- Initial implementation of audio streaming
- POST /stream-audio endpoint
- GET /stream-listen SSE endpoint
- Opus codec support
- Dual-slot streaming
- File-based circular buffer
- Live dashboard UI
