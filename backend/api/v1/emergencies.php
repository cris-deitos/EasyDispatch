<?php
/**
 * EasyDispatch API - Emergencies Endpoint
 * Handles emergency alert logging and management
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
        // Receive emergency alert
        $data = getJsonInput();
        
        $radioId = Validator::integer($data['radio_id'] ?? null);
        $emergencyType = Validator::string($data['emergency_type'] ?? 'generic', 1, 50);
        $latitude = isset($data['latitude']) ? Validator::latitude($data['latitude']) : null;
        $longitude = isset($data['longitude']) ? Validator::longitude($data['longitude']) : null;
        $triggeredAt = isset($data['triggered_at']) ? Validator::datetime($data['triggered_at']) : date('Y-m-d H:i:s');
        
        // Validate
        if ($radioId === false || $emergencyType === false || $triggeredAt === false) {
            sendError('Invalid or missing required fields: radio_id, emergency_type, triggered_at', 400);
        }
        
        // Insert emergency alert
        $stmt = $pdo->prepare("
            INSERT INTO dmr_emergencies (
                radio_id, emergency_type, latitude, longitude,
                triggered_at, status
            ) VALUES (?, ?, ?, ?, ?, 'active')
        ");
        
        $stmt->execute([
            $radioId,
            $emergencyType,
            $latitude,
            $longitude,
            $triggeredAt
        ]);
        
        $emergencyId = $pdo->lastInsertId();
        
        // Update radio status to emergency
        $updateStmt = $pdo->prepare("
            INSERT INTO dmr_radios (radio_id, status, last_seen)
            VALUES (?, 'emergency', NOW())
            ON DUPLICATE KEY UPDATE
                status = 'emergency',
                last_seen = NOW()
        ");
        $updateStmt->execute([$radioId]);
        
        // Log request
        logApiRequest(
            '/emergencies POST',
            $authInfo,
            "EMERGENCY: Radio $radioId - Type: $emergencyType"
        );
        
        sendSuccess(['emergency_id' => $emergencyId], 201);
        
    } elseif ($method === 'GET') {
        // Get emergency alerts
        $status = isset($_GET['status']) ? $_GET['status'] : 'active';
        $radioId = isset($_GET['radio_id']) ? Validator::integer($_GET['radio_id']) : null;
        $limit = Validator::integer($_GET['limit'] ?? 100, 1, 1000);
        
        $query = "
            SELECT 
                e.*,
                r.callsign,
                r.model,
                TIMESTAMPDIFF(MINUTE, e.triggered_at, NOW()) as minutes_active
            FROM dmr_emergencies e
            LEFT JOIN dmr_radios r ON e.radio_id = r.radio_id
            WHERE 1=1
        ";
        
        $params = [];
        
        if (Validator::enum($status, ['active', 'acknowledged', 'resolved'])) {
            $query .= " AND e.status = ?";
            $params[] = $status;
        }
        
        if ($radioId !== false && $radioId !== null) {
            $query .= " AND e.radio_id = ?";
            $params[] = $radioId;
        }
        
        $query .= " ORDER BY e.triggered_at DESC LIMIT ?";
        $params[] = $limit;
        
        $stmt = $pdo->prepare($query);
        $stmt->execute($params);
        $emergencies = $stmt->fetchAll();
        
        sendSuccess(['emergencies' => $emergencies, 'count' => count($emergencies)]);
        
    } else {
        sendError('Method not allowed', 405);
    }
    
} catch (PDOException $e) {
    error_log("Database error in emergencies.php: " . $e->getMessage());
    sendError('Database error', 500);
}
