<?php
/**
 * EasyDispatch Database Configuration
 */

// Database connection parameters
// For production, use environment variables or a separate config file
define('DB_HOST', getenv('DB_HOST') ?: 'localhost');
define('DB_NAME', getenv('DB_NAME') ?: 'easydispatch');
define('DB_USER', getenv('DB_USER') ?: 'easydispatch_api');
define('DB_PASS', getenv('DB_PASS') ?: 'your_secure_password_here');
define('DB_CHARSET', 'utf8mb4');

// PDO Connection
function getDatabaseConnection() {
    static $pdo = null;
    
    if ($pdo === null) {
        try {
            $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=" . DB_CHARSET;
            $options = [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
                PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES " . DB_CHARSET
            ];
            
            $pdo = new PDO($dsn, DB_USER, DB_PASS, $options);
            
        } catch (PDOException $e) {
            error_log("Database connection failed: " . $e->getMessage());
            http_response_code(500);
            echo json_encode([
                'success' => false,
                'error' => 'Database connection failed'
            ]);
            exit;
        }
    }
    
    return $pdo;
}

// Close database connection
function closeDatabaseConnection() {
    $pdo = null;
}
