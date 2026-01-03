<?php
/**
 * EasyDispatch API - Transmissions Endpoint
 * Handles voice and data transmission logging
 */

require_once __DIR__ . '/../middleware/cors.php';
require_once __DIR__ . '/../config/auth.php';
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../utils/response.php';
require_once __DIR__ . '/../utils/validator.php';
require_once __DIR__ . '/../middleware/rate_limiter.php';

// Authenticate
$authInfo = requireAuth();
applyRateLimit($authInfo['raspberry_id'], 200);

// Only allow POST
requireMethod('POST');

try {
    $pdo = getDatabaseConnection();
    
    // Get form data
    $radioId = Validator::integer($_POST['radio_id'] ?? null);
    $talkgroupId = isset($_POST['talkgroup_id']) ? Validator::integer($_POST['talkgroup_id']) : null;
    $timeslot = Validator::integer($_POST['timeslot'] ?? null, 1, 2);
    $startTime = Validator::datetime($_POST['start_time'] ?? '');
    $endTime = isset($_POST['end_time']) ? Validator::datetime($_POST['end_time']) : null;
    $duration = isset($_POST['duration']) ? Validator::integer($_POST['duration'], 0) : null;
    $rssi = isset($_POST['rssi']) ? Validator::integer($_POST['rssi']) : null;
    $ber = isset($_POST['ber']) ? Validator::float($_POST['ber'], 0, 100) : null;
    
    // Validate required fields
    if ($radioId === false || $timeslot === false || $startTime === false) {
        sendError('Invalid or missing required fields: radio_id, timeslot, start_time', 400);
    }
    
    // Handle audio file upload
    $audioFile = null;
    $audioSize = null;
    
    if (isset($_FILES['audio']) && $_FILES['audio']['error'] === UPLOAD_ERR_OK) {
        $uploadDir = __DIR__ . '/../../audio/';
        
        // Create audio directory if not exists
        if (!is_dir($uploadDir)) {
            mkdir($uploadDir, 0755, true);
        }
        
        // Generate unique filename
        $extension = pathinfo($_FILES['audio']['name'], PATHINFO_EXTENSION);
        $filename = sprintf(
            '%s_%d_slot%d_%s.%s',
            date('Ymd_His'),
            $radioId,
            $timeslot,
            uniqid(),
            $extension
        );
        
        $audioPath = $uploadDir . $filename;
        
        if (move_uploaded_file($_FILES['audio']['tmp_name'], $audioPath)) {
            $audioFile = 'audio/' . $filename;
            $audioSize = filesize($audioPath);
        } else {
            error_log("Failed to move uploaded file");
        }
    }
    
    // Insert transmission
    $stmt = $pdo->prepare("
        INSERT INTO dmr_transmissions (
            radio_id, talkgroup_id, timeslot, transmission_type,
            start_time, end_time, duration, audio_file, audio_size,
            rssi, ber
        ) VALUES (
            ?, ?, ?, 'voice',
            ?, ?, ?, ?, ?,
            ?, ?
        )
    ");
    
    $stmt->execute([
        $radioId,
        $talkgroupId,
        $timeslot,
        $startTime,
        $endTime,
        $duration,
        $audioFile,
        $audioSize,
        $rssi,
        $ber
    ]);
    
    $transmissionId = $pdo->lastInsertId();
    
    // Update radio status to online
    $updateStmt = $pdo->prepare("
        INSERT INTO dmr_radios (radio_id, status, last_seen, last_rssi, last_ber)
        VALUES (?, 'online', NOW(), ?, ?)
        ON DUPLICATE KEY UPDATE
            status = 'online',
            last_seen = NOW(),
            last_rssi = COALESCE(VALUES(last_rssi), last_rssi),
            last_ber = COALESCE(VALUES(last_ber), last_ber)
    ");
    $updateStmt->execute([$radioId, $rssi, $ber]);
    
    // Log request
    logApiRequest(
        '/transmissions',
        $authInfo,
        "Radio $radioId -> TG $talkgroupId, Duration: {$duration}s"
    );
    
    // Send response
    $response = [
        'transmission_id' => $transmissionId
    ];
    
    if ($audioFile) {
        $response['audio_url'] = 'https://' . $_SERVER['HTTP_HOST'] . '/' . $audioFile;
    }
    
    sendSuccess($response, 201);
    
} catch (PDOException $e) {
    error_log("Database error in transmissions.php: " . $e->getMessage());
    sendError('Database error', 500);
}
