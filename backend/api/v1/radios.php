<?php
/**
 * EasyDispatch API - Radios Endpoint
 * Handles radio registry queries
 */

require_once __DIR__ . '/../middleware/cors.php';
require_once __DIR__ . '/../config/auth.php';
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../utils/response.php';
require_once __DIR__ . '/../utils/validator.php';
require_once __DIR__ . '/../middleware/rate_limiter.php';

// Authenticate
$authInfo = requireAuth();
applyRateLimit($authInfo['raspberry_id'], 100);

// Only allow GET
requireMethod('GET');

try {
    $pdo = getDatabaseConnection();
    
    // Get query parameters
    $status = $_GET['status'] ?? null;
    $radioId = isset($_GET['radio_id']) ? Validator::integer($_GET['radio_id']) : null;
    $limit = Validator::integer($_GET['limit'] ?? 100, 1, 1000);
    $offset = Validator::integer($_GET['offset'] ?? 0, 0);
    
    $query = "
        SELECT 
            r.*,
            (SELECT COUNT(*) FROM dmr_transmissions t 
             WHERE t.radio_id = r.radio_id 
             AND t.start_time > DATE_SUB(NOW(), INTERVAL 24 HOUR)) as transmissions_24h,
            (SELECT MAX(p.timestamp) FROM dmr_gps_positions p 
             WHERE p.radio_id = r.radio_id) as last_gps_time
        FROM dmr_radios r
        WHERE 1=1
    ";
    
    $params = [];
    
    if ($status && Validator::enum($status, ['online', 'offline', 'emergency'])) {
        $query .= " AND r.status = ?";
        $params[] = $status;
    }
    
    if ($radioId !== false && $radioId !== null) {
        $query .= " AND r.radio_id = ?";
        $params[] = $radioId;
    }
    
    $query .= " ORDER BY r.last_seen DESC LIMIT ? OFFSET ?";
    $params[] = $limit;
    $params[] = $offset;
    
    $stmt = $pdo->prepare($query);
    $stmt->execute($params);
    $radios = $stmt->fetchAll();
    
    // Get total count
    $countQuery = "SELECT COUNT(*) as total FROM dmr_radios r WHERE 1=1";
    $countParams = [];
    
    if ($status && Validator::enum($status, ['online', 'offline', 'emergency'])) {
        $countQuery .= " AND r.status = ?";
        $countParams[] = $status;
    }
    
    if ($radioId !== false && $radioId !== null) {
        $countQuery .= " AND r.radio_id = ?";
        $countParams[] = $radioId;
    }
    
    $countStmt = $pdo->prepare($countQuery);
    $countStmt->execute($countParams);
    $total = $countStmt->fetch()['total'];
    
    sendSuccess([
        'radios' => $radios,
        'count' => count($radios),
        'total' => $total,
        'offset' => $offset,
        'limit' => $limit
    ]);
    
} catch (PDOException $e) {
    error_log("Database error in radios.php: " . $e->getMessage());
    sendError('Database error', 500);
}
