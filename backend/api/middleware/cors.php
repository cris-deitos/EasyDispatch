<?php
/**
 * EasyDispatch CORS Middleware
 * Handles Cross-Origin Resource Sharing
 */

// Allowed origins (configure based on your frontend)
$allowedOrigins = [
    'http://localhost',
    'http://localhost:3000',
    'http://localhost:8080',
    'https://your-dispatch-frontend.com'
];

// Get origin
$origin = isset($_SERVER['HTTP_ORIGIN']) ? $_SERVER['HTTP_ORIGIN'] : '';

// Check if origin is allowed
if (in_array($origin, $allowedOrigins)) {
    header('Access-Control-Allow-Origin: ' . $origin);
} else {
    // Default: allow all (change for production)
    header('Access-Control-Allow-Origin: *');
}

// Allowed methods
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');

// Allowed headers
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With');

// Credentials
header('Access-Control-Allow-Credentials: true');

// Max age for preflight cache
header('Access-Control-Max-Age: 86400'); // 24 hours

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}
