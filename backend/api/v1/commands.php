<?php
/**
 * EasyDispatch API - Commands Endpoint
 * Handles command queueing and completion
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
    
    if ($method === 'GET') {
        // Get pending commands for this Raspberry Pi
        $raspberryId = $_GET['raspberry_id'] ?? $authInfo['raspberry_id'];
        
        // Get pending commands
        $stmt = $pdo->prepare("
            SELECT 
                id,
                command_type,
                target_radio_id,
                target_talkgroup_id,
                payload,
                created_at
            FROM dmr_commands
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT 50
        ");
        
        $stmt->execute();
        $commands = $stmt->fetchAll();
        
        // Mark commands as sent
        if (!empty($commands)) {
            $commandIds = array_column($commands, 'id');
            $placeholders = implode(',', array_fill(0, count($commandIds), '?'));
            
            $updateStmt = $pdo->prepare("
                UPDATE dmr_commands
                SET status = 'sent', sent_at = NOW()
                WHERE id IN ($placeholders)
            ");
            $updateStmt->execute($commandIds);
            
            logApiRequest(
                '/commands GET',
                $authInfo,
                "Retrieved " . count($commands) . " pending commands"
            );
        }
        
        // Decode JSON payload for each command
        foreach ($commands as &$command) {
            if ($command['payload']) {
                $command['payload'] = json_decode($command['payload'], true);
            }
        }
        
        sendSuccess(['commands' => $commands, 'count' => count($commands)]);
        
    } elseif ($method === 'POST') {
        // Complete command execution
        // Extract command ID from path: /commands/{id}/complete
        $path = $_SERVER['REQUEST_URI'];
        if (preg_match('/\/commands\/(\d+)\/complete/', $path, $matches)) {
            $commandId = (int)$matches[1];
            
            $data = getJsonInput();
            $status = $data['status'] ?? '';
            $errorMessage = $data['error_message'] ?? null;
            
            // Validate
            if (!Validator::enum($status, ['completed', 'failed'])) {
                sendError('Invalid status. Must be: completed or failed', 400);
            }
            
            // Update command
            $stmt = $pdo->prepare("
                UPDATE dmr_commands
                SET status = ?, completed_at = NOW(), error_message = ?
                WHERE id = ?
            ");
            
            $stmt->execute([$status, $errorMessage, $commandId]);
            
            if ($stmt->rowCount() === 0) {
                sendError('Command not found', 404);
            }
            
            logApiRequest(
                "/commands/$commandId/complete",
                $authInfo,
                "Status: $status"
            );
            
            sendSuccess(['updated' => true]);
            
        } else {
            sendError('Invalid endpoint. Use /commands/{id}/complete', 400);
        }
        
    } else {
        sendError('Method not allowed', 405);
    }
    
} catch (PDOException $e) {
    error_log("Database error in commands.php: " . $e->getMessage());
    sendError('Database error', 500);
}
