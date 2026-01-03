<?php
/**
 * EasyDispatch API - Radio Status Endpoint
 * Handles radio status updates
 */

require_once __DIR__ . '/../middleware/cors.php';
require_once __DIR__ . '/../config/auth.php';
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../utils/response.php';
require_once __DIR__ . '/../utils/validator.php';
require_once __DIR__ . '/../middleware/rate_limiter.php';

// Authenticate
$authInfo = requireAuth();
applyRateLimit($authInfo['raspberry_id'], 500); // Higher limit for status updates

// Only allow POST
requireMethod('POST');

try {
    $pdo = getDatabaseConnection();
    
    $data = getJsonInput();
    
    $radioId = Validator::integer($data['radio_id'] ?? null);
    $status = $data['status'] ?? '';
    $rssi = isset($data['rssi']) ? Validator::integer($data['rssi']) : null;
    $ber = isset($data['ber']) ? Validator::float($data['ber'], 0, 100) : null;
    
    // Validate
    if ($radioId === false) {
        sendError('Invalid or missing required field: radio_id', 400);
    }
    
    if (!Validator::enum($status, ['online', 'offline', 'emergency'])) {
        sendError('Invalid status. Must be: online, offline, or emergency', 400);
    }
    
    // Update radio status
    $stmt = $pdo->prepare("
        INSERT INTO dmr_radios (radio_id, status, last_seen, last_rssi, last_ber)
        VALUES (?, ?, NOW(), ?, ?)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),
            last_seen = NOW(),
            last_rssi = COALESCE(VALUES(last_rssi), last_rssi),
            last_ber = COALESCE(VALUES(last_ber), last_ber)
    ");
    
    $stmt->execute([$radioId, $status, $rssi, $ber]);
    
    // Log request (only occasionally to avoid spam)
    if (rand(1, 10) === 1) {
        logApiRequest('/radio-status', $authInfo, "Radio $radioId -> $status");
    }
    
    sendSuccess(['updated' => true]);
    
} catch (PDOException $e) {
    error_log("Database error in radio-status.php: " . $e->getMessage());
    sendError('Database error', 500);
}
