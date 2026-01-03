-- EasyDispatch Database Schema
-- Complete schema for DMR dispatch system
-- Compatible with MySQL 5.7+ and MariaDB 10.2+

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

-- ============================================================================
-- DMR Radio Management
-- ============================================================================

CREATE TABLE IF NOT EXISTS `dmr_radios` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `radio_id` INT(11) NOT NULL UNIQUE COMMENT 'DMR ID Radio',
  `callsign` VARCHAR(20) DEFAULT NULL,
  `member_id` INT(11) DEFAULT NULL COMMENT 'Link a members di EasyVol',
  `model` VARCHAR(100) DEFAULT NULL,
  `serial_number` VARCHAR(100) DEFAULT NULL,
  `status` ENUM('online', 'offline', 'emergency') DEFAULT 'offline',
  `last_seen` TIMESTAMP NULL,
  `last_rssi` INT(11) DEFAULT NULL COMMENT 'Signal strength in dBm',
  `last_ber` FLOAT DEFAULT NULL COMMENT 'Bit Error Rate percentage',
  `notes` TEXT,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `radio_id` (`radio_id`),
  KEY `status` (`status`),
  KEY `last_seen` (`last_seen`),
  KEY `member_id` (`member_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='DMR Radio Registry';

-- ============================================================================
-- TalkGroups Configuration
-- ============================================================================

CREATE TABLE IF NOT EXISTS `dmr_talkgroups` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `tg_id` INT(11) NOT NULL UNIQUE COMMENT 'TalkGroup ID',
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT,
  `timeslot` TINYINT(1) DEFAULT NULL COMMENT '1 or 2, NULL for both',
  `is_active` TINYINT(1) DEFAULT 1,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `tg_id` (`tg_id`),
  KEY `is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='DMR TalkGroups';

-- Insert default talkgroups
INSERT INTO `dmr_talkgroups` (`tg_id`, `name`, `description`, `timeslot`) VALUES
(1, 'Worldwide', 'Worldwide TalkGroup', 1),
(2, 'Local', 'Local TalkGroup', 2),
(3, 'North America', 'North America TalkGroup', 1),
(8, 'Regional', 'Regional TalkGroup', 1),
(9, 'Local 9', 'Local 9 TalkGroup', 2),
(99, 'Simplex', 'Simplex TalkGroup', 1);

-- ============================================================================
-- Voice Transmissions
-- ============================================================================

CREATE TABLE IF NOT EXISTS `dmr_transmissions` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `radio_id` INT(11) NOT NULL,
  `talkgroup_id` INT(11) DEFAULT NULL,
  `timeslot` TINYINT(1) NOT NULL COMMENT '1 or 2',
  `transmission_type` ENUM('voice', 'data') DEFAULT 'voice',
  `start_time` DATETIME NOT NULL,
  `end_time` DATETIME DEFAULT NULL,
  `duration` INT(11) DEFAULT NULL COMMENT 'Duration in seconds',
  `audio_file` VARCHAR(500) DEFAULT NULL COMMENT 'Path to audio file',
  `audio_size` INT(11) DEFAULT NULL COMMENT 'File size in bytes',
  `rssi` INT(11) DEFAULT NULL COMMENT 'Signal strength in dBm',
  `ber` FLOAT DEFAULT NULL COMMENT 'Bit Error Rate percentage',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `radio_id` (`radio_id`),
  KEY `talkgroup_id` (`talkgroup_id`),
  KEY `start_time` (`start_time`),
  KEY `timeslot` (`timeslot`),
  KEY `transmission_type` (`transmission_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Voice and Data Transmissions';

-- ============================================================================
-- SMS Messages
-- ============================================================================

CREATE TABLE IF NOT EXISTS `dmr_sms` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `from_radio_id` INT(11) DEFAULT NULL,
  `to_radio_id` INT(11) DEFAULT NULL,
  `to_talkgroup_id` INT(11) DEFAULT NULL,
  `message` TEXT NOT NULL,
  `direction` ENUM('incoming', 'outgoing') NOT NULL,
  `sent_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delivered_at` TIMESTAMP NULL,
  `status` ENUM('pending', 'sent', 'delivered', 'failed') DEFAULT 'pending',
  `created_by_user_id` INT(11) DEFAULT NULL COMMENT 'User dispatcher who sent the message',
  PRIMARY KEY (`id`),
  KEY `from_radio_id` (`from_radio_id`),
  KEY `to_radio_id` (`to_radio_id`),
  KEY `to_talkgroup_id` (`to_talkgroup_id`),
  KEY `sent_at` (`sent_at`),
  KEY `status` (`status`),
  KEY `direction` (`direction`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='DMR SMS Messages';

-- ============================================================================
-- GPS Positions
-- ============================================================================

CREATE TABLE IF NOT EXISTS `dmr_gps_positions` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `radio_id` INT(11) NOT NULL,
  `latitude` DECIMAL(10, 8) NOT NULL,
  `longitude` DECIMAL(11, 8) NOT NULL,
  `altitude` INT(11) DEFAULT NULL COMMENT 'Altitude in meters',
  `speed` INT(11) DEFAULT NULL COMMENT 'Speed in km/h',
  `heading` INT(11) DEFAULT NULL COMMENT 'Heading in degrees 0-359',
  `accuracy` INT(11) DEFAULT NULL COMMENT 'Accuracy in meters',
  `timestamp` DATETIME NOT NULL COMMENT 'GPS timestamp',
  `received_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `radio_id` (`radio_id`),
  KEY `timestamp` (`timestamp`),
  KEY `received_at` (`received_at`),
  KEY `location` (`latitude`, `longitude`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='GPS Position History';

-- ============================================================================
-- Emergency Alerts
-- ============================================================================

CREATE TABLE IF NOT EXISTS `dmr_emergencies` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `radio_id` INT(11) NOT NULL,
  `emergency_type` VARCHAR(50) DEFAULT 'generic',
  `latitude` DECIMAL(10, 8) DEFAULT NULL,
  `longitude` DECIMAL(11, 8) DEFAULT NULL,
  `triggered_at` DATETIME NOT NULL,
  `received_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `acknowledged_at` DATETIME DEFAULT NULL,
  `acknowledged_by_user_id` INT(11) DEFAULT NULL,
  `resolved_at` DATETIME DEFAULT NULL,
  `resolved_by_user_id` INT(11) DEFAULT NULL,
  `notes` TEXT,
  `status` ENUM('active', 'acknowledged', 'resolved') DEFAULT 'active',
  PRIMARY KEY (`id`),
  KEY `radio_id` (`radio_id`),
  KEY `status` (`status`),
  KEY `triggered_at` (`triggered_at`),
  KEY `received_at` (`received_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Emergency Alerts';

-- ============================================================================
-- Remote Commands
-- ============================================================================

CREATE TABLE IF NOT EXISTS `dmr_commands` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `command_type` ENUM('sms', 'call_alert', 'gps_request', 'radio_check', 'remote_monitor') NOT NULL,
  `target_radio_id` INT(11) DEFAULT NULL,
  `target_talkgroup_id` INT(11) DEFAULT NULL,
  `payload` TEXT COMMENT 'JSON with command parameters',
  `status` ENUM('pending', 'sent', 'completed', 'failed') DEFAULT 'pending',
  `created_by_user_id` INT(11) NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `sent_at` TIMESTAMP NULL,
  `completed_at` TIMESTAMP NULL,
  `error_message` TEXT,
  PRIMARY KEY (`id`),
  KEY `status` (`status`),
  KEY `target_radio_id` (`target_radio_id`),
  KEY `created_at` (`created_at`),
  KEY `command_type` (`command_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Remote Commands Queue';

-- ============================================================================
-- System Configuration
-- ============================================================================

CREATE TABLE IF NOT EXISTS `dmr_system_config` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `parameter` VARCHAR(100) NOT NULL UNIQUE,
  `value` TEXT,
  `description` TEXT,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `parameter` (`parameter`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='System Configuration Parameters';

-- Insert default configuration
INSERT INTO `dmr_system_config` (`parameter`, `value`, `description`) VALUES
('system_name', 'EasyDispatch', 'System name'),
('audio_retention_days', '30', 'Days to retain audio files'),
('gps_retention_days', '90', 'Days to retain GPS history'),
('transmission_retention_days', '90', 'Days to retain transmission logs');

-- ============================================================================
-- API Keys
-- ============================================================================

CREATE TABLE IF NOT EXISTS `dmr_api_keys` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `key_name` VARCHAR(100) NOT NULL,
  `api_key` VARCHAR(64) NOT NULL UNIQUE,
  `raspberry_id` VARCHAR(50) DEFAULT NULL COMMENT 'Raspberry Pi identifier',
  `is_active` TINYINT(1) DEFAULT 1,
  `last_used_at` TIMESTAMP NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `api_key` (`api_key`),
  KEY `is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API Authentication Keys';

-- ============================================================================
-- Foreign Key Constraints (if members table exists)
-- ============================================================================

-- Uncomment if using with EasyVol or similar system with members table:
-- ALTER TABLE `dmr_radios`
--   ADD CONSTRAINT `dmr_radios_ibfk_1` FOREIGN KEY (`member_id`) REFERENCES `members`(`id`) ON DELETE SET NULL;

-- ============================================================================
-- Views for Quick Access
-- ============================================================================

-- Active radios view
CREATE OR REPLACE VIEW `dmr_radios_active` AS
SELECT 
  r.*,
  (SELECT COUNT(*) FROM dmr_transmissions t WHERE t.radio_id = r.radio_id AND t.start_time > DATE_SUB(NOW(), INTERVAL 24 HOUR)) as transmissions_24h
FROM dmr_radios r
WHERE r.status IN ('online', 'emergency')
  AND r.last_seen > DATE_SUB(NOW(), INTERVAL 5 MINUTE);

-- Recent transmissions view
CREATE OR REPLACE VIEW `dmr_transmissions_recent` AS
SELECT 
  t.*,
  r.callsign,
  tg.name as talkgroup_name
FROM dmr_transmissions t
LEFT JOIN dmr_radios r ON t.radio_id = r.radio_id
LEFT JOIN dmr_talkgroups tg ON t.talkgroup_id = tg.tg_id
WHERE t.start_time > DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY t.start_time DESC;

-- Active emergencies view
CREATE OR REPLACE VIEW `dmr_emergencies_active` AS
SELECT 
  e.*,
  r.callsign,
  r.model,
  TIMESTAMPDIFF(MINUTE, e.triggered_at, NOW()) as minutes_active
FROM dmr_emergencies e
LEFT JOIN dmr_radios r ON e.radio_id = r.radio_id
WHERE e.status = 'active'
ORDER BY e.triggered_at DESC;

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Additional composite indexes for common queries
CREATE INDEX idx_transmissions_radio_time ON dmr_transmissions(radio_id, start_time);
CREATE INDEX idx_transmissions_tg_time ON dmr_transmissions(talkgroup_id, start_time);
CREATE INDEX idx_gps_radio_time ON dmr_gps_positions(radio_id, timestamp);
CREATE INDEX idx_sms_direction_status ON dmr_sms(direction, status);

-- ============================================================================
-- Stored Procedures
-- ============================================================================

DELIMITER //

-- Update radio status
CREATE PROCEDURE `update_radio_status`(
  IN p_radio_id INT,
  IN p_status VARCHAR(20),
  IN p_rssi INT,
  IN p_ber FLOAT
)
BEGIN
  INSERT INTO dmr_radios (radio_id, status, last_seen, last_rssi, last_ber)
  VALUES (p_radio_id, p_status, NOW(), p_rssi, p_ber)
  ON DUPLICATE KEY UPDATE
    status = p_status,
    last_seen = NOW(),
    last_rssi = COALESCE(p_rssi, last_rssi),
    last_ber = COALESCE(p_ber, last_ber);
END//

-- Get pending commands for Raspberry Pi
CREATE PROCEDURE `get_pending_commands`(
  IN p_raspberry_id VARCHAR(50)
)
BEGIN
  SELECT 
    c.id,
    c.command_type,
    c.target_radio_id,
    c.target_talkgroup_id,
    c.payload,
    c.created_at
  FROM dmr_commands c
  WHERE c.status = 'pending'
  ORDER BY c.created_at ASC
  LIMIT 50;
  
  -- Mark as sent
  UPDATE dmr_commands
  SET status = 'sent', sent_at = NOW()
  WHERE status = 'pending'
  ORDER BY created_at ASC
  LIMIT 50;
END//

-- Cleanup old data
CREATE PROCEDURE `cleanup_old_data`()
BEGIN
  DECLARE audio_days INT;
  DECLARE gps_days INT;
  DECLARE trans_days INT;
  
  -- Get retention settings
  SELECT CAST(value AS UNSIGNED) INTO audio_days FROM dmr_system_config WHERE parameter = 'audio_retention_days';
  SELECT CAST(value AS UNSIGNED) INTO gps_days FROM dmr_system_config WHERE parameter = 'gps_retention_days';
  SELECT CAST(value AS UNSIGNED) INTO trans_days FROM dmr_system_config WHERE parameter = 'transmission_retention_days';
  
  -- Delete old GPS positions
  DELETE FROM dmr_gps_positions 
  WHERE timestamp < DATE_SUB(NOW(), INTERVAL gps_days DAY);
  
  -- Delete old transmissions (without audio)
  DELETE FROM dmr_transmissions 
  WHERE start_time < DATE_SUB(NOW(), INTERVAL trans_days DAY)
    AND audio_file IS NULL;
    
  -- Mark old transmissions with audio for cleanup
  UPDATE dmr_transmissions 
  SET audio_file = CONCAT('TO_DELETE_', audio_file)
  WHERE start_time < DATE_SUB(NOW(), INTERVAL audio_days DAY)
    AND audio_file IS NOT NULL
    AND audio_file NOT LIKE 'TO_DELETE_%';
END//

DELIMITER ;

-- ============================================================================
-- Events for Automatic Maintenance
-- ============================================================================

-- Enable event scheduler
SET GLOBAL event_scheduler = ON;

-- Cleanup event (runs daily at 3 AM)
CREATE EVENT IF NOT EXISTS `event_daily_cleanup`
ON SCHEDULE EVERY 1 DAY
STARTS (TIMESTAMP(CURRENT_DATE) + INTERVAL 1 DAY + INTERVAL 3 HOUR)
DO CALL cleanup_old_data();

-- Mark offline radios (runs every 5 minutes)
CREATE EVENT IF NOT EXISTS `event_mark_offline_radios`
ON SCHEDULE EVERY 5 MINUTE
DO
  UPDATE dmr_radios
  SET status = 'offline'
  WHERE status = 'online'
    AND last_seen < DATE_SUB(NOW(), INTERVAL 10 MINUTE);

-- ============================================================================
-- Grants (adjust based on your setup)
-- ============================================================================

-- Example grants for API user (adjust username/password)
-- CREATE USER 'easydispatch_api'@'localhost' IDENTIFIED BY 'secure_password_here';
-- GRANT SELECT, INSERT, UPDATE ON easydispatch.dmr_* TO 'easydispatch_api'@'localhost';
-- FLUSH PRIVILEGES;

-- ============================================================================
-- Schema Version
-- ============================================================================

INSERT INTO `dmr_system_config` (`parameter`, `value`, `description`) VALUES
('schema_version', '1.0.0', 'Database schema version')
ON DUPLICATE KEY UPDATE value = '1.0.0';
