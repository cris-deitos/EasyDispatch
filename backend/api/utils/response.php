<?php
/**
 * EasyDispatch API Response Helper
 */

/**
 * Send JSON success response
 * @param mixed $data Response data
 * @param int $code HTTP status code
 */
function sendSuccess($data, $code = 200) {
    http_response_code($code);
    header('Content-Type: application/json');
    
    $response = ['success' => true];
    if (is_array($data)) {
        $response = array_merge($response, $data);
    } else {
        $response['data'] = $data;
    }
    
    echo json_encode($response);
    exit;
}

/**
 * Send JSON error response
 * @param string $message Error message
 * @param int $code HTTP status code
 * @param array $details Additional error details
 */
function sendError($message, $code = 400, $details = []) {
    http_response_code($code);
    header('Content-Type: application/json');
    
    $response = [
        'success' => false,
        'error' => $message
    ];
    
    if (!empty($details)) {
        $response['details'] = $details;
    }
    
    echo json_encode($response);
    exit;
}

/**
 * Get request method
 * @return string HTTP method (GET, POST, etc.)
 */
function getRequestMethod() {
    return $_SERVER['REQUEST_METHOD'];
}

/**
 * Check if request method is allowed
 * @param string|array $allowedMethods Allowed method(s)
 */
function requireMethod($allowedMethods) {
    if (!is_array($allowedMethods)) {
        $allowedMethods = [$allowedMethods];
    }
    
    $method = getRequestMethod();
    
    if (!in_array($method, $allowedMethods)) {
        http_response_code(405);
        header('Allow: ' . implode(', ', $allowedMethods));
        sendError('Method not allowed', 405);
    }
}

/**
 * Get JSON input data
 * @return array Parsed JSON data
 */
function getJsonInput() {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        sendError('Invalid JSON input', 400);
    }
    
    return $data ?: [];
}

/**
 * Get POST/GET parameter
 * @param string $key Parameter key
 * @param mixed $default Default value
 * @return mixed Parameter value
 */
function getParam($key, $default = null) {
    if (getRequestMethod() === 'GET') {
        return isset($_GET[$key]) ? $_GET[$key] : $default;
    } else {
        // For POST, check both $_POST and JSON input
        if (isset($_POST[$key])) {
            return $_POST[$key];
        }
        
        $json = getJsonInput();
        return isset($json[$key]) ? $json[$key] : $default;
    }
}

/**
 * Log API request
 * @param string $endpoint Endpoint accessed
 * @param array $authInfo Authentication info
 * @param string $details Additional details
 */
function logApiRequest($endpoint, $authInfo, $details = '') {
    $logFile = __DIR__ . '/../../logs/api_' . date('Y-m-d') . '.log';
    $logDir = dirname($logFile);
    
    if (!is_dir($logDir)) {
        mkdir($logDir, 0755, true);
    }
    
    $logEntry = sprintf(
        "[%s] %s %s - API Key: %s (%s) - %s\n",
        date('Y-m-d H:i:s'),
        $_SERVER['REQUEST_METHOD'],
        $endpoint,
        $authInfo['key_name'],
        $authInfo['raspberry_id'] ?: 'N/A',
        $details
    );
    
    file_put_contents($logFile, $logEntry, FILE_APPEND);
}
