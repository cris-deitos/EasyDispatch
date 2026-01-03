# EasyDispatch - Complete DMR Dispatch System

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)

**EasyDispatch** is a complete end-to-end system for managing a DMR dispatch operation on a Raspberry Pi with MMDVM hardware. It provides real-time monitoring, audio recording, GPS tracking, emergency alerts, and remote command capabilities for DMR radio networks.

## 🚀 Features

### Raspberry Pi Side (Python)
- **Real-time DMR Traffic Monitoring** - Monitor all DMR transmissions on both timeslots
- **Dual-Slot Audio Capture** - Record audio from both timeslots simultaneously
- **Data Parsing** - Decode SMS, GPS, emergency alerts, and telemetry
- **API Integration** - Seamless communication with backend hosting
- **Remote Commands** - Execute commands from dispatch center
- **Custom Frequencies** - Support for any VHF/UHF frequency within hardware limits
- **OLED Display** - Real-time status display on integrated OLED

### Backend Side (PHP)
- **RESTful API** - Complete API for data collection and command dispatch
- **Real-time Dashboard** - Monitor all radio activity
- **GPS Tracking** - Track radio positions on map
- **Emergency Management** - Instant emergency alert notifications
- **SMS Messaging** - Send and receive DMR SMS messages
- **Audio Playback** - Listen to recorded transmissions
- **Radio Registry** - Manage radio fleet
- **User Management** - Multi-user dispatch center support

## 📋 Requirements

### Hardware
- **Raspberry Pi 3 Model B v1.2** (or newer)
- **MMDVM_HS_Dual_Hat** - Duplex MMDVM Hotspot (UHF/VHF)
- **MicroSD Card** - 16GB minimum, 32GB recommended
- **Power Supply** - 5V 2.5A minimum
- **Antenna** - Dual-band VHF/UHF antenna

### Software
- Raspberry Pi OS (Bookworm or newer)
- Python 3.9+
- PHP 7.4+
- MySQL 5.7+ or MariaDB 10.2+
- Apache or Nginx web server

## 🛠️ Installation

### Quick Start - Raspberry Pi

One-line installation:

```bash
curl -sSL https://raw.githubusercontent.com/cris-deitos/EasyDispatch/main/raspberry/scripts/install.sh | sudo bash
```

This will:
1. Update system packages
2. Install all dependencies
3. Compile MMDVM software
4. Install EasyDispatch collector
5. Configure system
6. Reboot

After reboot, configure MMDVM:

```bash
sudo bash /etc/mmdvm-templates/configure.sh
```

Then configure EasyDispatch:

```bash
sudo nano /etc/easydispatch/config.yaml
```

Start services:

```bash
sudo systemctl start mmdvmhost
sudo systemctl start easydispatch-collector
```

### Backend Installation

1. **Import database schema:**

```bash
mysql -u root -p easydispatch < backend/database/schema.sql
```

2. **Configure database connection:**

Edit `backend/api/config/database.php`:

```php
define('DB_HOST', 'localhost');
define('DB_NAME', 'easydispatch');
define('DB_USER', 'easydispatch_api');
define('DB_PASS', 'your_secure_password');
```

3. **Set up web server:**

For Apache:

```apache
<VirtualHost *:80>
    ServerName easydispatch.local
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

4. **Generate API key:**

```sql
INSERT INTO dmr_api_keys (key_name, api_key, raspberry_id, is_active)
VALUES ('Raspberry Pi Station 1', SHA2(CONCAT(UUID(), RAND()), 256), 'RASP001', 1);
```

5. **Configure Raspberry Pi with API key:**

Update `/etc/easydispatch/config.yaml` with the generated API key.

## 📖 Documentation

- **[Hardware Setup Guide](raspberry/docs/HARDWARE_SETUP.md)** - Detailed hardware assembly instructions
- **[Installation Guide](raspberry/docs/INSTALLATION.md)** - Complete installation walkthrough
- **[Frequency Configuration](raspberry/docs/FREQUENCY_CONFIG.md)** - Custom frequency setup guide

## 🗂️ Project Structure

```
EasyDispatch/
├── raspberry/                    # Raspberry Pi components
│   ├── image-builder/           # SD card image builder
│   ├── mmdvm-config/            # MMDVM configuration templates
│   ├── easydispatch-collector/  # Main Python application
│   │   ├── collector/           # Core modules
│   │   │   ├── dmr_monitor.py
│   │   │   ├── audio_capture.py
│   │   │   ├── data_parser.py
│   │   │   ├── api_client.py
│   │   │   └── command_handler.py
│   │   ├── config/              # Configuration files
│   │   ├── systemd/             # Service files
│   │   └── main.py
│   ├── scripts/                 # Utility scripts
│   └── docs/                    # Documentation
│
└── backend/                      # Backend API & Web Interface
    ├── api/                      # RESTful API
    │   ├── config/              # Configuration
    │   ├── v1/                  # API v1 endpoints
    │   ├── middleware/          # CORS & rate limiting
    │   └── utils/               # Helper functions
    ├── audio/                    # Audio file storage
    ├── logs/                     # API logs
    └── database/                 # Database schemas
        ├── schema.sql
        └── migrations/
```

## 🔌 API Endpoints

### Transmissions
- `POST /api/v1/transmissions` - Log voice transmission

### SMS
- `POST /api/v1/sms` - Log received SMS
- `GET /api/v1/sms` - Get SMS history

### GPS
- `POST /api/v1/gps` - Log GPS position
- `GET /api/v1/gps` - Get position history

### Emergencies
- `POST /api/v1/emergencies` - Log emergency alert
- `GET /api/v1/emergencies` - Get active emergencies

### Radio Status
- `POST /api/v1/radio-status` - Update radio status

### Commands
- `GET /api/v1/commands` - Poll for pending commands
- `POST /api/v1/commands/{id}/complete` - Mark command complete

### Radios
- `GET /api/v1/radios` - Get radio registry

## 🔐 Security

- **API Authentication** - Bearer token authentication
- **Rate Limiting** - Prevents API abuse
- **Input Validation** - All inputs sanitized
- **SQL Injection Protection** - Prepared statements
- **File Upload Security** - Validated and sanitized uploads

## 🛡️ Database Schema

The system uses 8 main tables:

- `dmr_radios` - Radio registry
- `dmr_talkgroups` - TalkGroup configuration
- `dmr_transmissions` - Voice/data transmissions
- `dmr_sms` - SMS messages
- `dmr_gps_positions` - GPS tracking
- `dmr_emergencies` - Emergency alerts
- `dmr_commands` - Remote commands
- `dmr_api_keys` - API authentication

See [schema.sql](backend/database/schema.sql) for complete structure.

## 🎯 Use Cases

- **Emergency Services** - Dispatch and track emergency vehicles
- **Private Organizations** - Fleet management and communication
- **Event Management** - Coordinate staff during events
- **Security Operations** - Monitor security teams
- **Industrial Operations** - Track and communicate with field workers

## 🔧 Configuration

### Raspberry Pi Configuration

Edit `/etc/easydispatch/config.yaml`:

```yaml
raspberry:
  id: "RASP001"
  dmr_id: 2222000

api:
  endpoint: "https://your-server.com/api/v1"
  key: "your_api_key_here"

audio:
  capture_device: "plughw:0,0"
  sample_rate: 8000
  compression: "mp3"

polling:
  commands_interval: 10
  status_update_interval: 60
```

### MMDVM Configuration

Run interactive configuration:

```bash
sudo bash /etc/mmdvm-templates/configure.sh
```

Or edit `/etc/mmdvm/MMDVM.ini` manually.

## 📊 Monitoring

Check system status:

```bash
sudo easydispatch-status
```

View logs:

```bash
# Collector logs
sudo journalctl -u easydispatch-collector -f

# MMDVM logs
tail -f /var/log/mmdvm/MMDVM.log
```

Monitor resources:

```bash
htop
vcgencmd measure_temp
df -h
```

## 🔄 Maintenance

### Backup Configuration

```bash
sudo easydispatch-backup
```

### Update System

```bash
sudo apt-get update && sudo apt-get upgrade
```

### Update EasyDispatch

```bash
cd /tmp
git clone https://github.com/cris-deitos/EasyDispatch.git
sudo cp -r EasyDispatch/raspberry/easydispatch-collector/* /opt/easydispatch/
sudo systemctl restart easydispatch-collector
```

### Clean Old Audio Files

```bash
sudo find /var/lib/easydispatch/audio -type f -mtime +30 -delete
```

## 🐛 Troubleshooting

### Service Won't Start

```bash
sudo systemctl status easydispatch-collector
sudo journalctl -u easydispatch-collector -n 50
```

### No Audio Capture

```bash
arecord -l
arecord -D plughw:0,0 -d 5 -f S16_LE -r 8000 test.wav
```

### Cannot Connect to API

```bash
curl -I https://your-server.com/api/v1/radios
ping your-server.com
```

See [INSTALLATION.md](raspberry/docs/INSTALLATION.md) for more troubleshooting tips.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 💡 Support

For issues, questions, or feature requests:
- **GitHub Issues**: https://github.com/cris-deitos/EasyDispatch/issues
- **Documentation**: https://github.com/cris-deitos/EasyDispatch

## ⚠️ Legal Notice

- Ensure you have proper authorization for all frequencies used
- Follow local regulations for RF transmission
- Some frequencies require specific licenses or certifications
- Never transmit on emergency services frequencies without authorization

## 🙏 Acknowledgments

- MMDVMHost project for excellent DMR implementation
- Raspberry Pi Foundation for the platform
- DMR community for protocols and documentation

## 📅 Version History

### v1.0.0 (2026-01-03)
- Initial release
- Complete Raspberry Pi collector implementation
- Full backend API implementation
- Comprehensive documentation
- Support for custom VHF/UHF frequencies
- Dual-slot audio capture
- GPS tracking
- Emergency alerts
- Remote commands

---

**Made with ❤️ for the DMR dispatch community**