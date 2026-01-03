<?php
/**
 * EasyDispatch Rate Limiter Middleware
 * Prevents API abuse
 */

class RateLimiter {
    private $maxRequests;
    private $timeWindow;
    private $storageFile;
    
    /**
     * Constructor
     * @param int $maxRequests Maximum requests per time window
     * @param int $timeWindow Time window in seconds
     */
    public function __construct($maxRequests = 100, $timeWindow = 60) {
        $this->maxRequests = $maxRequests;
        $this->timeWindow = $timeWindow;
        $this->storageFile = __DIR__ . '/../../logs/rate_limit.json';
    }
    
    /**
     * Check rate limit for client
     * @param string $identifier Client identifier (IP or API key)
     * @return bool True if within limit, false if exceeded
     */
    public function checkLimit($identifier) {
        $data = $this->loadData();
        $now = time();
        
        // Clean old entries
        $data = $this->cleanOldEntries($data, $now);
        
        // Initialize client data if not exists
        if (!isset($data[$identifier])) {
            $data[$identifier] = [
                'requests' => [],
                'blocked_until' => 0
            ];
        }
        
        // Check if client is blocked
        if ($data[$identifier]['blocked_until'] > $now) {
            return false;
        }
        
        // Add current request
        $data[$identifier]['requests'][] = $now;
        
        // Keep only requests within time window
        $data[$identifier]['requests'] = array_filter(
            $data[$identifier]['requests'],
            function($timestamp) use ($now) {
                return ($now - $timestamp) <= $this->timeWindow;
            }
        );
        
        // Check if limit exceeded
        $requestCount = count($data[$identifier]['requests']);
        
        if ($requestCount > $this->maxRequests) {
            // Block for time window duration
            $data[$identifier]['blocked_until'] = $now + $this->timeWindow;
            $this->saveData($data);
            return false;
        }
        
        $this->saveData($data);
        return true;
    }
    
    /**
     * Get remaining requests for client
     * @param string $identifier Client identifier
     * @return int Remaining requests
     */
    public function getRemainingRequests($identifier) {
        $data = $this->loadData();
        $now = time();
        
        if (!isset($data[$identifier])) {
            return $this->maxRequests;
        }
        
        // Count requests within time window
        $recentRequests = array_filter(
            $data[$identifier]['requests'],
            function($timestamp) use ($now) {
                return ($now - $timestamp) <= $this->timeWindow;
            }
        );
        
        return max(0, $this->maxRequests - count($recentRequests));
    }
    
    /**
     * Load rate limit data from storage
     * @return array Rate limit data
     */
    private function loadData() {
        if (!file_exists($this->storageFile)) {
            return [];
        }
        
        $content = file_get_contents($this->storageFile);
        $data = json_decode($content, true);
        
        return $data ?: [];
    }
    
    /**
     * Save rate limit data to storage
     * @param array $data Rate limit data
     */
    private function saveData($data) {
        $dir = dirname($this->storageFile);
        if (!is_dir($dir)) {
            mkdir($dir, 0755, true);
        }
        
        file_put_contents($this->storageFile, json_encode($data));
    }
    
    /**
     * Clean old entries from data
     * @param array $data Rate limit data
     * @param int $now Current timestamp
     * @return array Cleaned data
     */
    private function cleanOldEntries($data, $now) {
        foreach ($data as $identifier => $clientData) {
            // Remove if all requests are old and not blocked
            if (empty($clientData['requests']) && $clientData['blocked_until'] < $now) {
                unset($data[$identifier]);
                continue;
            }
            
            // Filter old requests
            $data[$identifier]['requests'] = array_filter(
                $clientData['requests'],
                function($timestamp) use ($now) {
                    return ($now - $timestamp) <= $this->timeWindow * 2;
                }
            );
        }
        
        return $data;
    }
}

/**
 * Apply rate limiting
 * @param string $identifier Client identifier
 * @param int $maxRequests Maximum requests per minute
 */
function applyRateLimit($identifier, $maxRequests = 100) {
    $rateLimiter = new RateLimiter($maxRequests, 60);
    
    if (!$rateLimiter->checkLimit($identifier)) {
        http_response_code(429);
        header('Content-Type: application/json');
        echo json_encode([
            'success' => false,
            'error' => 'Rate limit exceeded',
            'message' => 'Too many requests. Please try again later.'
        ]);
        exit;
    }
    
    // Add rate limit headers
    $remaining = $rateLimiter->getRemainingRequests($identifier);
    header('X-RateLimit-Limit: ' . $maxRequests);
    header('X-RateLimit-Remaining: ' . $remaining);
}
