<?php
/**
 * EasyDispatch Input Validator
 */

class Validator {
    
    /**
     * Validate required fields
     * @param array $data Input data
     * @param array $required Required field names
     * @return array|null Array of missing fields or null if all present
     */
    public static function required($data, $required) {
        $missing = [];
        
        foreach ($required as $field) {
            if (!isset($data[$field]) || $data[$field] === '' || $data[$field] === null) {
                $missing[] = $field;
            }
        }
        
        return empty($missing) ? null : $missing;
    }
    
    /**
     * Validate integer
     * @param mixed $value Value to validate
     * @param int $min Minimum value
     * @param int $max Maximum value
     * @return bool|int False or validated integer
     */
    public static function integer($value, $min = null, $max = null) {
        if (!is_numeric($value)) {
            return false;
        }
        
        $int = (int)$value;
        
        if ($min !== null && $int < $min) {
            return false;
        }
        
        if ($max !== null && $int > $max) {
            return false;
        }
        
        return $int;
    }
    
    /**
     * Validate float
     * @param mixed $value Value to validate
     * @param float $min Minimum value
     * @param float $max Maximum value
     * @return bool|float False or validated float
     */
    public static function float($value, $min = null, $max = null) {
        if (!is_numeric($value)) {
            return false;
        }
        
        $float = (float)$value;
        
        if ($min !== null && $float < $min) {
            return false;
        }
        
        if ($max !== null && $float > $max) {
            return false;
        }
        
        return $float;
    }
    
    /**
     * Validate datetime
     * @param string $value Datetime string
     * @return bool|string False or validated datetime string
     */
    public static function datetime($value) {
        $formats = [
            'Y-m-d H:i:s',
            'Y-m-d\TH:i:s',
            'Y-m-d\TH:i:s\Z',
            'Y-m-d H:i:s.u'
        ];
        
        foreach ($formats as $format) {
            $date = DateTime::createFromFormat($format, $value);
            if ($date !== false) {
                return $date->format('Y-m-d H:i:s');
            }
        }
        
        return false;
    }
    
    /**
     * Validate enum value
     * @param mixed $value Value to validate
     * @param array $allowed Allowed values
     * @return bool
     */
    public static function enum($value, $allowed) {
        return in_array($value, $allowed, true);
    }
    
    /**
     * Validate latitude
     * @param mixed $value Latitude value
     * @return bool|float False or validated latitude
     */
    public static function latitude($value) {
        $lat = self::float($value, -90, 90);
        return $lat !== false ? $lat : false;
    }
    
    /**
     * Validate longitude
     * @param mixed $value Longitude value
     * @return bool|float False or validated longitude
     */
    public static function longitude($value) {
        $lon = self::float($value, -180, 180);
        return $lon !== false ? $lon : false;
    }
    
    /**
     * Validate string length
     * @param string $value String value
     * @param int $min Minimum length
     * @param int $max Maximum length
     * @return bool|string False or validated string
     */
    public static function string($value, $min = null, $max = null) {
        if (!is_string($value)) {
            return false;
        }
        
        $len = mb_strlen($value);
        
        if ($min !== null && $len < $min) {
            return false;
        }
        
        if ($max !== null && $len > $max) {
            return false;
        }
        
        return $value;
    }
    
    /**
     * Sanitize filename
     * @param string $filename Filename
     * @return string Sanitized filename
     */
    public static function sanitizeFilename($filename) {
        // Remove path components
        $filename = basename($filename);
        
        // Remove special characters
        $filename = preg_replace('/[^a-zA-Z0-9._-]/', '_', $filename);
        
        return $filename;
    }
}
