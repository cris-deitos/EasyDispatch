<?php
/**
 * EasyDispatch API - GPS Endpoint
 * Handles GPS position logging and retrieval
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

$method = getRequestMethod();

try {
    $pdo = getDatabaseConnection();
    
    if ($method === 'POST') {
        // Receive GPS position
        $data = getJsonInput();
        
        $radioId = Validator::integer($data['radio_id'] ?? null);
        $latitude = Validator::latitude($data['latitude'] ?? null);
        $longitude = Validator::longitude($data['longitude'] ?? null);
        $altitude = isset($data['altitude']) ? Validator::integer($data['altitude']) : null;
        $speed = isset($data['speed']) ? Validator::integer($data['speed'], 0) : null;
        $heading = isset($data['heading']) ? Validator::integer($data['heading'], 0, 359) : null;
        $accuracy = isset($data['accuracy']) ? Validator::integer($data['accuracy'], 0) : null;
        $timestamp = isset($data['timestamp']) ? Validator::datetime($data['timestamp']) : date('Y-m-d H:i:s');
        
        // Validate
        if ($radioId === false || $latitude === false || $longitude === false || $timestamp === false) {
            sendError('Invalid or missing required fields: radio_id, latitude, longitude, timestamp', 400);
        }
        
        // Insert GPS position
        $stmt = $pdo->prepare("
            INSERT INTO dmr_gps_positions (
                radio_id, latitude, longitude, altitude,
                speed, heading, accuracy, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ");
        
        $stmt->execute([
            $radioId,
            $latitude,
            $longitude,
            $altitude,
            $speed,
            $heading,
            $accuracy,
            $timestamp
        ]);
        
        $positionId = $pdo->lastInsertId();
        
        // Log request
        logApiRequest(
            '/gps POST',
            $authInfo,
            "Radio $radioId at $latitude, $longitude"
        );
        
        sendSuccess(['position_id' => $positionId], 201);
        
    } elseif ($method === 'GET') {
        // Get GPS history
        $radioId = Validator::integer($_GET['radio_id'] ?? null);
        $since = isset($_GET['since']) ? Validator::datetime($_GET['since']) : null;
        $limit = Validator::integer($_GET['limit'] ?? 100, 1, 1000);
        
        $query = "
            SELECT 
                p.*,
                r.callsign
            FROM dmr_gps_positions p
            LEFT JOIN dmr_radios r ON p.radio_id = r.radio_id
        ";
        
        $conditions = [];
        $params = [];
        
        if ($radioId !== false) {
            $conditions[] = "p.radio_id = ?";
            $params[] = $radioId;
        }
        
        if ($since !== false && $since !== null) {
            $conditions[] = "p.timestamp >= ?";
            $params[] = $since;
        }
        
        if (!empty($conditions)) {
            $query .= " WHERE " . implode(' AND ', $conditions);
        }
        
        $query .= " ORDER BY p.timestamp DESC LIMIT ?";
        $params[] = $limit;
        
        $stmt = $pdo->prepare($query);
        $stmt->execute($params);
        $positions = $stmt->fetchAll();
        
        sendSuccess(['positions' => $positions, 'count' => count($positions)]);
        
    } else {
        sendError('Method not allowed', 405);
    }
    
} catch (PDOException $e) {
    error_log("Database error in gps.php: " . $e->getMessage());
    sendError('Database error', 500);
}
