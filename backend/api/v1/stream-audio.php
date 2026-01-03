<?php
/**
 * Stream Audio Endpoint
 * Receives real-time audio chunks from Raspberry Pi
 */

header('Content-Type: application/json');

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/auth.php';
require_once __DIR__ . '/../middleware/rate_limiter.php';
require_once __DIR__ . '/../utils/response.php';
require_once __DIR__ . '/../utils/validator.php';

// Enable rate limiting (more permissive for streaming)
$rateLimiter = new RateLimiter();
if (!$rateLimiter->check($_SERVER['REMOTE_ADDR'], 1000, 60)) {
    Response::error('Rate limit exceeded', 429);
}

// Authenticate request
$authResult = authenticate();
if (!$authResult['success']) {
    Response::error($authResult['message'], 401);
}

// Only accept POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    Response::error('Method not allowed', 405);
}

// Parse JSON body
$input = json_decode(file_get_contents('php://input'), true);

// Validate input
$requiredFields = ['slot', 'radio_id', 'talkgroup_id', 'chunk_data', 'sequence'];
foreach ($requiredFields as $field) {
    if (!isset($input[$field])) {
        Response::error("Missing required field: {$field}", 400);
    }
}

$slot = (int)$input['slot'];
$radio_id = (int)$input['radio_id'];
$talkgroup_id = (int)$input['talkgroup_id'];
$chunk_data = $input['chunk_data'];
$sequence = (int)$input['sequence'];
$timestamp = $input['timestamp'] ?? date('Y-m-d H:i:s');

// Validate slot
if (!in_array($slot, [1, 2])) {
    Response::error('Invalid slot (must be 1 or 2)', 400);
}

// Validate base64
if (!base64_decode($chunk_data, true)) {
    Response::error('Invalid chunk_data (not valid base64)', 400);
}

try {
    // Buffer directory structure
    $bufferDir = __DIR__ . '/../../tmp/audio_buffers';
    if (!is_dir($bufferDir)) {
        mkdir($bufferDir, 0755, true);
    }
    
    // Create slot-specific buffer directory
    $slotDir = $bufferDir . "/slot{$slot}";
    if (!is_dir($slotDir)) {
        mkdir($slotDir, 0755, true);
    }
    
    # Transmission identifier (unique per transmission session)
    // Use radio_id and talkgroup as part of ID to maintain consistency
    $transmissionKey = "r{$radio_id}_tg{$talkgroup_id}";
    $metaFile = $slotDir . "/current_meta.json";
    
    // Load existing metadata to get or create transmission ID
    $transmissionId = null;
    if (file_exists($metaFile)) {
        $existingMeta = json_decode(file_get_contents($metaFile), true);
        // Reuse ID if same radio/TG and recent (within 5 seconds)
        if ($existingMeta && 
            $existingMeta['radio_id'] == $radio_id &&
            $existingMeta['talkgroup_id'] == $talkgroup_id &&
            (time() - $existingMeta['last_update']) < 5) {
            $transmissionId = $existingMeta['transmission_id'];
        }
    }
    
    // Create new transmission ID if needed
    if (!$transmissionId) {
        $transmissionId = $transmissionKey . '_' . date('YmdHis');
    }
    
    // Chunk file path
    $chunkFile = $slotDir . "/{$transmissionId}_{$sequence}.opus";
    
    // Decode and save chunk
    $chunkBinary = base64_decode($chunk_data);
    if ($chunkBinary === false) {
        Response::error('Failed to decode chunk data', 400);
    }
    
    file_put_contents($chunkFile, $chunkBinary);
    
    // Update metadata file
    $metaFile = $slotDir . "/current_meta.json";
    $metadata = [
        'transmission_id' => $transmissionId,
        'slot' => $slot,
        'radio_id' => $radio_id,
        'talkgroup_id' => $talkgroup_id,
        'last_sequence' => $sequence,
        'last_update' => time(),
        'timestamp' => $timestamp
    ];
    file_put_contents($metaFile, json_encode($metadata));
    
    // Cleanup old chunks (keep last 50) - only run occasionally
    // Run cleanup only 10% of the time to reduce overhead
    if (rand(1, 10) === 1) {
        $files = glob($slotDir . "/*.opus");
        if (count($files) > 50) {
            usort($files, function($a, $b) {
                return filemtime($a) - filemtime($b);
            });
            $filesToDelete = array_slice($files, 0, count($files) - 50);
            foreach ($filesToDelete as $file) {
                @unlink($file);
            }
        }
    }
    
    // Optional: Store in database for permanent recording
    if (isset($input['save_recording']) && $input['save_recording']) {
        $db = getDbConnection();
        
        // Check if transmission exists
        $stmt = $db->prepare("
            SELECT id FROM dmr_transmissions 
            WHERE radio_id = ? AND timeslot = ? 
            AND start_time > DATE_SUB(NOW(), INTERVAL 5 SECOND)
            ORDER BY start_time DESC LIMIT 1
        ");
        $stmt->bind_param('ii', $radio_id, $slot);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows === 0) {
            // Create new transmission record
            $stmt = $db->prepare("
                INSERT INTO dmr_transmissions 
                (radio_id, talkgroup_id, timeslot, transmission_type, start_time)
                VALUES (?, ?, ?, 'voice', NOW())
            ");
            $stmt->bind_param('iii', $radio_id, $talkgroup_id, $slot);
            $stmt->execute();
        }
        
        $stmt->close();
        $db->close();
    }
    
    Response::success([
        'received' => true,
        'slot' => $slot,
        'sequence' => $sequence,
        'size' => strlen($chunkBinary)
    ]);
    
} catch (Exception $e) {
    error_log("Stream audio error: " . $e->getMessage());
    Response::error('Internal server error', 500);
}
