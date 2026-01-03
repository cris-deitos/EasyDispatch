<?php
/**
 * EasyDispatch API Authentication
 */

require_once __DIR__ . '/database.php';

/**
 * Authenticate API request using Bearer token
 * @return array|false Array with API key info or false if authentication fails
 */
function authenticateRequest() {
    $headers = getallheaders();
    
    // Get Authorization header
    $authHeader = null;
    if (isset($headers['Authorization'])) {
        $authHeader = $headers['Authorization'];
    } elseif (isset($headers['authorization'])) {
        $authHeader = $headers['authorization'];
    }
    
    if (!$authHeader) {
        return false;
    }
    
    // Extract token from "Bearer TOKEN" format
    if (preg_match('/Bearer\s+(.+)/i', $authHeader, $matches)) {
        $apiKey = $matches[1];
    } else {
        return false;
    }
    
    // Validate API key in database
    try {
        $pdo = getDatabaseConnection();
        
        $stmt = $pdo->prepare("
            SELECT id, key_name, raspberry_id, is_active 
            FROM dmr_api_keys 
            WHERE api_key = ? AND is_active = 1
        ");
        $stmt->execute([$apiKey]);
        $keyInfo = $stmt->fetch();
        
        if (!$keyInfo) {
            return false;
        }
        
        // Update last used timestamp
        $updateStmt = $pdo->prepare("
            UPDATE dmr_api_keys 
            SET last_used_at = NOW() 
            WHERE id = ?
        ");
        $updateStmt->execute([$keyInfo['id']]);
        
        return $keyInfo;
        
    } catch (PDOException $e) {
        error_log("Authentication error: " . $e->getMessage());
        return false;
    }
}

/**
 * Require authentication or return 401
 * @return array API key info
 */
function requireAuth() {
    $authInfo = authenticateRequest();
    
    if (!$authInfo) {
        http_response_code(401);
        echo json_encode([
            'success' => false,
            'error' => 'Unauthorized',
            'message' => 'Invalid or missing API key'
        ]);
        exit;
    }
    
    return $authInfo;
}

/**
 * Generate new API key
 * @return string New API key
 */
function generateApiKey() {
    return bin2hex(random_bytes(32));
}
