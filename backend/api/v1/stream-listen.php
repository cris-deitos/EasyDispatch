<?php
/**
 * Stream Listen Endpoint
 * Server-Sent Events (SSE) endpoint for browser audio streaming
 */

// SSE headers
header('Content-Type: text/event-stream');
header('Cache-Control: no-cache');
header('Connection: keep-alive');
header('X-Accel-Buffering: no'); // Disable nginx buffering

// Flush output immediately
ob_end_flush();
flush();

// Disable time limit for SSE
set_time_limit(0);

// Get slot from query parameter
$slot = isset($_GET['slot']) ? (int)$_GET['slot'] : 1;

// Validate slot
if (!in_array($slot, [1, 2])) {
    echo "event: error\n";
    echo "data: {\"error\": \"Invalid slot\"}\n\n";
    flush();
    exit;
}

// Buffer directory
$bufferDir = __DIR__ . '/../../tmp/audio_buffers/slot' . $slot;
if (!is_dir($bufferDir)) {
    mkdir($bufferDir, 0755, true);
}

$metaFile = $bufferDir . '/current_meta.json';
$lastSequence = -1;
$lastTransmissionId = null;
$keepAliveInterval = 15; // seconds
$lastKeepAlive = time();
$timeout = 300; // 5 minutes

$startTime = time();

// Send initial connection message
echo "event: connected\n";
echo "data: {\"slot\": $slot, \"message\": \"Connected to slot $slot\"}\n\n";
flush();

// Main SSE loop
while (true) {
    // Check timeout
    if (time() - $startTime > $timeout) {
        echo "event: timeout\n";
        echo "data: {\"message\": \"Connection timeout\"}\n\n";
        flush();
        break;
    }
    
    // Send keep-alive
    if (time() - $lastKeepAlive >= $keepAliveInterval) {
        echo "event: keepalive\n";
        echo "data: {\"timestamp\": " . time() . "}\n\n";
        flush();
        $lastKeepAlive = time();
    }
    
    // Check for metadata updates
    if (file_exists($metaFile)) {
        clearstatcache(true, $metaFile);
        $metadata = json_decode(file_get_contents($metaFile), true);
        
        if ($metadata) {
            $currentTransmissionId = $metadata['transmission_id'] ?? null;
            $currentSequence = $metadata['last_sequence'] ?? -1;
            
            // Check if new transmission started
            if ($currentTransmissionId !== $lastTransmissionId) {
                // Send transmission start event
                echo "event: transmission_start\n";
                echo "data: " . json_encode([
                    'transmission_id' => $currentTransmissionId,
                    'slot' => $metadata['slot'],
                    'radio_id' => $metadata['radio_id'],
                    'talkgroup_id' => $metadata['talkgroup_id'],
                    'timestamp' => $metadata['timestamp'] ?? null
                ]) . "\n\n";
                flush();
                
                $lastTransmissionId = $currentTransmissionId;
                $lastSequence = -1;
            }
            
            // Check if metadata was updated recently (within last 5 seconds)
            $lastUpdate = $metadata['last_update'] ?? 0;
            if (time() - $lastUpdate > 5) {
                // Transmission likely ended
                if ($lastTransmissionId !== null) {
                    echo "event: transmission_end\n";
                    echo "data: {\"transmission_id\": \"$lastTransmissionId\"}\n\n";
                    flush();
                    $lastTransmissionId = null;
                    $lastSequence = -1;
                }
            } else {
                // Active transmission - check for new chunks
                if ($currentSequence > $lastSequence) {
                    // Find and send new chunks
                    for ($seq = $lastSequence + 1; $seq <= $currentSequence; $seq++) {
                        $chunkFile = $bufferDir . "/{$currentTransmissionId}_{$seq}.opus";
                        
                        if (file_exists($chunkFile)) {
                            $chunkData = file_get_contents($chunkFile);
                            $chunkBase64 = base64_encode($chunkData);
                            
                            echo "event: audio_chunk\n";
                            echo "data: " . json_encode([
                                'sequence' => $seq,
                                'chunk' => $chunkBase64,
                                'size' => strlen($chunkData)
                            ]) . "\n\n";
                            flush();
                        }
                    }
                    
                    $lastSequence = $currentSequence;
                }
            }
        }
    }
    
    // Check if client disconnected
    if (connection_aborted()) {
        break;
    }
    
    // Small delay to prevent CPU spinning
    usleep(50000); // 50ms
}

// Cleanup on disconnect
echo "event: disconnected\n";
echo "data: {\"message\": \"Stream ended\"}\n\n";
flush();
