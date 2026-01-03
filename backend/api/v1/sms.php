<?php
/**
 * EasyDispatch API - SMS Endpoint
 * Handles SMS message logging and retrieval
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
        // Receive incoming SMS
        $data = getJsonInput();
        
        $fromRadioId = Validator::integer($data['from_radio_id'] ?? null);
        $toRadioId = isset($data['to_radio_id']) ? Validator::integer($data['to_radio_id']) : null;
        $toTalkgroupId = isset($data['to_talkgroup_id']) ? Validator::integer($data['to_talkgroup_id']) : null;
        $message = Validator::string($data['message'] ?? '', 1, 1000);
        $timestamp = isset($data['timestamp']) ? Validator::datetime($data['timestamp']) : date('Y-m-d H:i:s');
        
        // Validate
        if ($fromRadioId === false || $message === false) {
            sendError('Invalid or missing required fields: from_radio_id, message', 400);
        }
        
        if ($toRadioId === false && $toTalkgroupId === false) {
            sendError('Must specify either to_radio_id or to_talkgroup_id', 400);
        }
        
        // Insert SMS
        $stmt = $pdo->prepare("
            INSERT INTO dmr_sms (
                from_radio_id, to_radio_id, to_talkgroup_id,
                message, direction, sent_at, status
            ) VALUES (?, ?, ?, ?, 'incoming', ?, 'delivered')
        ");
        
        $stmt->execute([
            $fromRadioId,
            $toRadioId,
            $toTalkgroupId,
            $message,
            $timestamp
        ]);
        
        $smsId = $pdo->lastInsertId();
        
        // Log request
        $target = $toRadioId ? "Radio $toRadioId" : "TG $toTalkgroupId";
        logApiRequest(
            '/sms POST',
            $authInfo,
            "From Radio $fromRadioId to $target"
        );
        
        sendSuccess(['sms_id' => $smsId], 201);
        
    } elseif ($method === 'GET') {
        // Get SMS history
        $radioId = Validator::integer($_GET['radio_id'] ?? null);
        $limit = Validator::integer($_GET['limit'] ?? 50, 1, 1000);
        $offset = Validator::integer($_GET['offset'] ?? 0, 0);
        
        $query = "
            SELECT 
                s.*,
                r1.callsign as from_callsign,
                r2.callsign as to_callsign,
                tg.name as to_talkgroup_name
            FROM dmr_sms s
            LEFT JOIN dmr_radios r1 ON s.from_radio_id = r1.radio_id
            LEFT JOIN dmr_radios r2 ON s.to_radio_id = r2.radio_id
            LEFT JOIN dmr_talkgroups tg ON s.to_talkgroup_id = tg.tg_id
        ";
        
        $params = [];
        
        if ($radioId !== false) {
            $query .= " WHERE (s.from_radio_id = ? OR s.to_radio_id = ?)";
            $params[] = $radioId;
            $params[] = $radioId;
        }
        
        $query .= " ORDER BY s.sent_at DESC LIMIT ? OFFSET ?";
        $params[] = $limit;
        $params[] = $offset;
        
        $stmt = $pdo->prepare($query);
        $stmt->execute($params);
        $messages = $stmt->fetchAll();
        
        sendSuccess(['messages' => $messages, 'count' => count($messages)]);
        
    } else {
        sendError('Method not allowed', 405);
    }
    
} catch (PDOException $e) {
    error_log("Database error in sms.php: " . $e->getMessage());
    sendError('Database error', 500);
}
