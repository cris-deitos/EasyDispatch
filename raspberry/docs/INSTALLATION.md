# EasyDispatch Installation Guide

## Prerequisites

- Assembled hardware (see [HARDWARE_SETUP.md](HARDWARE_SETUP.md))
- MicroSD card (16GB minimum, 32GB recommended)
- Computer with SD card reader
- Internet connection
- Basic Linux command line knowledge

## Installation Methods

### Method 1: One-Line Installation (Recommended)

For a Raspberry Pi with Raspberry Pi OS already installed:

```bash
curl -sSL https://raw.githubusercontent.com/cris-deitos/EasyDispatch/main/raspberry/scripts/install.sh | sudo bash
```

This will:
1. Update the system
2. Install all dependencies
3. Compile MMDVM software
4. Install EasyDispatch collector
5. Configure services
6. Reboot the system

**Time required:** 30-60 minutes (depending on internet speed)

### Method 2: Custom Image (Advanced)

Build a custom SD card image with everything pre-installed:

```bash
# On a Linux computer (not Raspberry Pi)
sudo bash raspberry/image-builder/build-image.sh
```

Then write the image to SD card:

```bash
xzcat easydispatch-YYYYMMDD.img.xz | sudo dd of=/dev/sdX bs=4M status=progress
```

Replace `/dev/sdX` with your SD card device.

### Method 3: Manual Installation (Advanced)

Follow the steps in `install.sh` manually if you need custom configuration.

## Post-Installation Configuration

### Step 1: Configure MMDVM Frequencies

Run the interactive configuration script:

```bash
sudo bash /etc/mmdvm-templates/configure.sh
```

You will be prompted for:
- Callsign (e.g., IU2ABC)
- DMR ID (e.g., 2222000)
- RX Frequency in MHz (e.g., 433.4500)
- TX Frequency in MHz (e.g., 434.4500)
- Latitude (decimal, e.g., 45.464664)
- Longitude (decimal, e.g., 9.188540)
- Location (e.g., Milano, IT)

The script will:
- Generate `/etc/mmdvm/MMDVM.ini`
- Generate `/etc/mmdvm/DMRGateway.ini`
- Validate configuration

See [FREQUENCY_CONFIG.md](FREQUENCY_CONFIG.md) for detailed frequency information.

### Step 2: Configure EasyDispatch Collector

Edit the collector configuration:

```bash
sudo nano /etc/easydispatch/config.yaml
```

Required settings:

```yaml
raspberry:
  id: "RASP001"  # Unique ID for this Raspberry Pi
  dmr_id: 2222000  # Same as MMDVM

api:
  endpoint: "https://your-hosting.com/easydispatch/api/v1"
  key: "YOUR_API_KEY_HERE"  # Get from backend
  raspberry_id: "RASP001"
```

Optional settings (defaults are usually fine):

```yaml
audio:
  capture_device: "plughw:0,0"
  sample_rate: 8000
  compression: "mp3"
  bitrate: 64

polling:
  commands_interval: 10  # Check for commands every 10 seconds
  status_update_interval: 60  # Update status every 60 seconds
```

### Step 3: Obtain API Key

1. Log into your EasyDispatch backend admin panel
2. Navigate to: **System** → **DMR Configuration** → **API Keys**
3. Click **Generate New API Key**
4. Name it (e.g., "Raspberry Pi Station 1")
5. Copy the generated key
6. Paste it into `/etc/easydispatch/config.yaml`

### Step 4: Start Services

Start MMDVM services:

```bash
sudo systemctl start mmdvmhost
sudo systemctl start dmrgateway
```

Start EasyDispatch collector:

```bash
sudo systemctl start easydispatch-collector
```

### Step 5: Verify Operation

Check system status:

```bash
sudo easydispatch-status
```

or use individual commands:

```bash
# Check MMDVMHost
sudo systemctl status mmdvmhost

# Check EasyDispatch Collector
sudo systemctl status easydispatch-collector

# View logs
sudo journalctl -u easydispatch-collector -f
```

Monitor MMDVM logs:

```bash
tail -f /var/log/mmdvm/MMDVM.log
```

## Network Configuration

### Ethernet (Recommended)

1. Connect Ethernet cable
2. System will auto-configure via DHCP
3. Find IP: `ip addr show eth0`

### WiFi

Edit WiFi configuration:

```bash
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Add your network:

```
network={
    ssid="YourNetworkName"
    psk="YourPassword"
}
```

Restart networking:

```bash
sudo systemctl restart networking
```

### Static IP (Optional)

Edit `/etc/dhcpcd.conf`:

```bash
sudo nano /etc/dhcpcd.conf
```

Add:

```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

## Firewall Configuration

The installation script configures UFW (Uncomplicated Firewall):

- SSH (22/tcp) - allowed
- DMRGateway (62031/udp) - allowed
- MMDVMHost (62032/udp) - allowed

To add more rules:

```bash
sudo ufw allow <port>/<protocol>
sudo ufw reload
```

## Automatic Updates

Enable automatic security updates:

```bash
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

Select "Yes" when prompted.

## Backup Configuration

Create a backup:

```bash
sudo easydispatch-backup
```

Backups are stored in `/var/lib/easydispatch/backups/`

Restore from backup:

```bash
sudo tar -xzf /var/lib/easydispatch/backups/easydispatch-backup-YYYYMMDD_HHMMSS.tar.gz -C /
sudo systemctl restart mmdvmhost easydispatch-collector
```

## Maintenance

### Update EasyDispatch

```bash
cd /tmp
git clone https://github.com/cris-deitos/EasyDispatch.git
sudo cp -r EasyDispatch/raspberry/easydispatch-collector/* /opt/easydispatch/
sudo systemctl restart easydispatch-collector
```

### Update MMDVM

```bash
cd /tmp/MMDVMHost
git pull
make clean && make
sudo make install
sudo systemctl restart mmdvmhost
```

### Update System

```bash
sudo apt-get update
sudo apt-get upgrade
sudo reboot
```

### View Logs

```bash
# Collector logs
sudo journalctl -u easydispatch-collector -f

# MMDVM logs
tail -f /var/log/mmdvm/MMDVM.log

# System logs
sudo journalctl -f
```

### Monitor Resource Usage

```bash
# CPU and memory
htop

# Disk usage
df -h

# Temperature
vcgencmd measure_temp
```

## Troubleshooting

### Service Won't Start

```bash
# Check status
sudo systemctl status easydispatch-collector

# Check for errors in logs
sudo journalctl -u easydispatch-collector -n 50

# Verify configuration
sudo python3 -c "import yaml; yaml.safe_load(open('/etc/easydispatch/config.yaml'))"
```

### No Audio Capture

```bash
# List audio devices
arecord -l

# Test audio capture
arecord -D plughw:0,0 -d 5 -f S16_LE -r 8000 test.wav
aplay test.wav
```

### Cannot Connect to API

```bash
# Test network connectivity
ping -c 3 8.8.8.8

# Test API endpoint (replace with your URL)
curl -I https://your-hosting.com

# Check API key in config
grep "key:" /etc/easydispatch/config.yaml
```

### High CPU Usage

```bash
# Check processes
top

# Reduce log level in config.yaml
sudo nano /etc/easydispatch/config.yaml
# Change: level: "INFO" (was DEBUG)

sudo systemctl restart easydispatch-collector
```

### Disk Space Full

```bash
# Check disk usage
df -h

# Clean old audio files
sudo find /var/lib/easydispatch/audio -type f -mtime +7 -delete

# Clean old logs
sudo journalctl --vacuum-time=7d
```

## Security Best Practices

1. **Change default passwords**
   ```bash
   passwd
   ```

2. **Use SSH keys instead of passwords**
   ```bash
   ssh-keygen
   # Copy public key to authorized_keys
   ```

3. **Keep system updated**
   ```bash
   sudo apt-get update && sudo apt-get upgrade
   ```

4. **Monitor logs regularly**
   ```bash
   sudo easydispatch-status
   ```

5. **Use strong API keys**
   - Minimum 32 characters
   - Use backend-generated keys

## Next Steps

1. Monitor system for 24 hours to ensure stability
2. Configure additional radios in backend
3. Set up talkgroups
4. Test SMS and GPS functionality
5. Configure emergency alerts
6. Train operators on system use

## Support

For issues or questions:
- GitHub Issues: https://github.com/cris-deitos/EasyDispatch/issues
- Documentation: https://github.com/cris-deitos/EasyDispatch
