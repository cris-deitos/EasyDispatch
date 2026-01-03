# EasyDispatch Quick Start Guide

This guide will help you get EasyDispatch up and running in minimal time.

## Prerequisites Checklist

- [ ] Raspberry Pi 3 Model B (or newer) with power supply
- [ ] MMDVM_HS_Dual_Hat installed on Raspberry Pi
- [ ] VHF/UHF antenna connected
- [ ] 16GB+ microSD card
- [ ] Network connection (Ethernet or WiFi)
- [ ] Web hosting with PHP 7.4+ and MySQL 5.7+

## Step 1: Raspberry Pi Setup (30-60 minutes)

### 1.1 Flash Raspberry Pi OS

1. Download [Raspberry Pi OS Lite](https://www.raspberrypi.com/software/)
2. Flash to microSD card using [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
3. Insert card into Raspberry Pi
4. Connect network cable (or configure WiFi)
5. Power on Raspberry Pi

### 1.2 Initial Connection

SSH into Raspberry Pi (default password: `raspberry`):

```bash
ssh pi@raspberrypi.local
```

Change default password:

```bash
passwd
```

### 1.3 Run Installation Script

```bash
curl -sSL https://raw.githubusercontent.com/cris-deitos/EasyDispatch/main/raspberry/scripts/install.sh | sudo bash
```

**Wait 30-60 minutes for installation to complete. System will reboot automatically.**

### 1.4 Configure MMDVM

After reboot, SSH back in and configure MMDVM:

```bash
sudo bash /etc/mmdvm-templates/configure.sh
```

Enter when prompted:
- **Callsign**: Your callsign (e.g., IU2ABC)
- **DMR ID**: Your DMR ID (e.g., 2222001)
- **RX Frequency**: Receive frequency in MHz (e.g., 433.4500)
- **TX Frequency**: Transmit frequency in MHz (e.g., 434.4500)
- **Latitude**: Location latitude (e.g., 45.464664)
- **Longitude**: Location longitude (e.g., 9.188540)
- **Location**: Location description (e.g., Milano, IT)

## Step 2: Backend Setup (15 minutes)

### 2.1 Database Setup

On your web server:

```bash
# Create database
mysql -u root -p << EOF
CREATE DATABASE easydispatch CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'easydispatch_api'@'localhost' IDENTIFIED BY 'CHOOSE_SECURE_PASSWORD';
GRANT SELECT, INSERT, UPDATE ON easydispatch.* TO 'easydispatch_api'@'localhost';
FLUSH PRIVILEGES;
EOF

# Import schema
mysql -u root -p easydispatch < backend/database/schema.sql
```

### 2.2 Upload Backend Files

Upload the `backend` directory to your web server:

```bash
scp -r backend/ user@yourserver:/var/www/easydispatch/
```

### 2.3 Configure Database Connection

Edit `backend/api/config/database.php`:

```php
define('DB_HOST', 'localhost');
define('DB_NAME', 'easydispatch');
define('DB_USER', 'easydispatch_api');
define('DB_PASS', 'YOUR_SECURE_PASSWORD');
```

### 2.4 Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/easydispatch
sudo chmod -R 755 /var/www/easydispatch
sudo chmod 777 /var/www/easydispatch/backend/audio
sudo chmod 777 /var/www/easydispatch/backend/logs
```

### 2.5 Configure Web Server

**Apache:**

```bash
sudo nano /etc/apache2/sites-available/easydispatch.conf
```

```apache
<VirtualHost *:80>
    ServerName easydispatch.yourdomain.com
    DocumentRoot /var/www/easydispatch/backend
    
    <Directory /var/www/easydispatch/backend>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ErrorLog ${APACHE_LOG_DIR}/easydispatch_error.log
    CustomLog ${APACHE_LOG_DIR}/easydispatch_access.log combined
</VirtualHost>
```

Enable site:

```bash
sudo a2ensite easydispatch
sudo a2enmod rewrite
sudo systemctl reload apache2
```

### 2.6 Generate API Key

```bash
mysql -u root -p easydispatch << EOF
INSERT INTO dmr_api_keys (key_name, api_key, raspberry_id, is_active)
VALUES (
    'Raspberry Pi Station 1',
    SHA2(CONCAT(UUID(), RAND()), 256),
    'RASP001',
    1
);
SELECT api_key FROM dmr_api_keys WHERE key_name = 'Raspberry Pi Station 1';
EOF
```

**Copy the generated API key!**

## Step 3: Connect Raspberry Pi to Backend (5 minutes)

### 3.1 Configure Collector

On Raspberry Pi, edit configuration:

```bash
sudo nano /etc/easydispatch/config.yaml
```

Update these values:

```yaml
raspberry:
  id: "RASP001"
  dmr_id: 2222001  # Your DMR ID

api:
  endpoint: "https://easydispatch.yourdomain.com/api/v1"
  key: "PASTE_YOUR_API_KEY_HERE"
  raspberry_id: "RASP001"
```

### 3.2 Start Services

```bash
sudo systemctl start mmdvmhost
sudo systemctl start easydispatch-collector
```

### 3.3 Verify Operation

```bash
sudo easydispatch-status
```

You should see:
- MMDVMHost: ✓ Running
- EasyDispatch Collector: ✓ Running
- Internet connection: ✓ OK
- API host: ✓ Reachable

## Step 4: Test System (5 minutes)

### 4.1 Test DMR Transmission

Use a DMR radio to transmit on your configured frequency. You should see:

1. **On Raspberry Pi**: Log entry in `/var/log/mmdvm/MMDVM.log`
2. **On Backend**: New entry in `dmr_transmissions` table
3. **Audio File**: Created in `backend/audio/` directory

Check logs:

```bash
# Raspberry Pi
sudo journalctl -u easydispatch-collector -f

# Backend (on server)
tail -f /var/www/easydispatch/backend/logs/api_*.log
```

### 4.2 Verify Database

On backend server:

```bash
mysql -u root -p easydispatch << EOF
SELECT * FROM dmr_radios;
SELECT * FROM dmr_transmissions ORDER BY start_time DESC LIMIT 5;
EOF
```

You should see your radio and recent transmissions.

### 4.3 Test API Endpoint

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://easydispatch.yourdomain.com/api/v1/radios
```

Should return JSON with radio list.

## Step 5: Configure Radios (Optional)

### 5.1 Add Radio Information

Update radio info in database:

```sql
UPDATE dmr_radios 
SET callsign = 'IU2ABC', 
    model = 'Hytera PD785G',
    notes = 'Vehicle 1'
WHERE radio_id = 2222001;
```

### 5.2 Configure TalkGroups

```sql
INSERT INTO dmr_talkgroups (tg_id, name, description, timeslot)
VALUES 
    (10, 'Operations', 'Main operations channel', 1),
    (11, 'Logistics', 'Logistics coordination', 2);
```

## Troubleshooting

### Raspberry Pi Issues

**Service won't start:**
```bash
sudo systemctl status easydispatch-collector
sudo journalctl -u easydispatch-collector -n 50
```

**No MMDVM communication:**
```bash
sudo systemctl status mmdvmhost
tail -f /var/log/mmdvm/MMDVM.log
```

**No audio capture:**
```bash
arecord -l  # List audio devices
arecord -D plughw:0,0 -d 5 test.wav  # Test recording
```

### Backend Issues

**Database connection error:**
- Verify credentials in `database.php`
- Check MySQL is running: `sudo systemctl status mysql`
- Test connection: `mysql -u easydispatch_api -p easydispatch`

**API returns 401:**
- Verify API key in database
- Check API key in Raspberry Pi config
- Verify `is_active = 1` in `dmr_api_keys`

**Audio files not saved:**
- Check directory permissions: `ls -la backend/audio/`
- Should be writable by web server user (www-data)

### Network Issues

**Cannot reach API:**
```bash
# On Raspberry Pi
ping easydispatch.yourdomain.com
curl -I https://easydispatch.yourdomain.com/api/v1/radios
```

**Firewall blocking:**
```bash
# On server
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## Next Steps

1. **Monitor System**: Keep an eye on logs for first 24 hours
2. **Add More Radios**: Register additional radios in database
3. **Configure Alerts**: Set up emergency alert notifications
4. **Backup Configuration**: Run `sudo easydispatch-backup`
5. **Build Frontend**: Create web interface using the API
6. **Train Users**: Train dispatch operators on the system

## Support

- **Documentation**: See `raspberry/docs/` for detailed guides
- **Issues**: https://github.com/cris-deitos/EasyDispatch/issues
- **Logs**: Check `/var/log/easydispatch/` and `/var/log/mmdvm/`

## System Architecture

```
┌─────────────────┐
│   DMR Radio     │ 
│   (Transmit)    │ 
└────────┬────────┘
         │ RF Signal
         ↓
┌─────────────────────────────┐
│  Raspberry Pi + MMDVM Hat   │
│  - DMR Monitor              │
│  - Audio Capture            │
│  - Data Parser              │
│  - API Client               │
└────────┬────────────────────┘
         │ HTTPS API Calls
         ↓
┌─────────────────────────────┐
│  Backend Server (PHP)       │
│  - REST API                 │
│  - Database (MySQL)         │
│  - Audio Storage            │
│  - Web Interface            │
└─────────────────────────────┘
         │
         ↓
┌─────────────────────────────┐
│  Dispatch Operators         │
│  - Monitor Activity         │
│  - Send Commands            │
│  - Track GPS                │
│  - Handle Emergencies       │
└─────────────────────────────┘
```

**Congratulations! Your EasyDispatch system is now operational! 🎉**
