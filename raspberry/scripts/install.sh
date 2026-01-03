#!/bin/bash
# EasyDispatch Complete Installation Script
# Automated installation for Raspberry Pi

set -e

INSTALL_DIR="/opt/easydispatch"
CONFIG_DIR="/etc/easydispatch"
LOG_DIR="/var/log/easydispatch"
LIB_DIR="/var/lib/easydispatch"

echo "============================================"
echo "EasyDispatch Automated Installation"
echo "============================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Updating system..."
apt-get update
apt-get upgrade -y

echo ""
echo "Step 2: Installing dependencies..."
apt-get install -y \
    build-essential git cmake make g++ gcc \
    python3 python3-pip python3-dev python3-venv \
    sox libsox-fmt-all ffmpeg alsa-utils libasound2-dev \
    python3-serial python3-rpi.gpio python3-smbus \
    curl wget net-tools dnsutils \
    htop iotop vnstat \
    i2c-tools python3-pil \
    logrotate jq

echo ""
echo "Step 3: Installing Python packages..."
pip3 install --upgrade pip
pip3 install PyYAML requests pyserial

echo ""
echo "Step 4: Compiling MMDVMHost..."
cd /tmp
if [ ! -d "MMDVMHost" ]; then
    git clone https://github.com/g4klx/MMDVMHost.git
fi
cd MMDVMHost
git pull
make clean
make
make install

echo ""
echo "Step 5: Compiling DMRGateway..."
cd /tmp
if [ ! -d "DMRGateway" ]; then
    git clone https://github.com/g4klx/DMRGateway.git
fi
cd DMRGateway
git pull
make clean
make
make install

echo ""
echo "Step 6: Installing MMDVM_HS_Dual_Hat driver..."
# Enable SPI and I2C
raspi-config nonint do_spi 0
raspi-config nonint do_i2c 0

# Configure device tree overlays
if ! grep -q "dtoverlay=pi3-disable-bt" /boot/config.txt; then
    echo "dtoverlay=pi3-disable-bt" >> /boot/config.txt
fi
if ! grep -q "enable_uart=1" /boot/config.txt; then
    echo "enable_uart=1" >> /boot/config.txt
fi

# Disable Bluetooth UART
systemctl disable hciuart 2>/dev/null || true
systemctl stop serial-getty@ttyAMA0.service 2>/dev/null || true
systemctl disable serial-getty@ttyAMA0.service 2>/dev/null || true

echo ""
echo "Step 7: Creating EasyDispatch directories..."
mkdir -p "${INSTALL_DIR}"
mkdir -p "${CONFIG_DIR}"
mkdir -p "${LOG_DIR}"
mkdir -p "${LIB_DIR}"
mkdir -p "${LIB_DIR}/audio"

echo ""
echo "Step 8: Installing EasyDispatch Collector..."
# Clone or copy EasyDispatch repository
cd /tmp
if [ ! -d "EasyDispatch" ]; then
    git clone https://github.com/cris-deitos/EasyDispatch.git
else
    cd EasyDispatch
    git pull
    cd ..
fi

# Copy collector files
cp -r EasyDispatch/raspberry/easydispatch-collector/* "${INSTALL_DIR}/"
cp -r EasyDispatch/raspberry/mmdvm-config /etc/mmdvm-templates

# Install Python package
cd "${INSTALL_DIR}"
pip3 install -r requirements.txt

echo ""
echo "Step 9: Creating configuration files..."
# Copy example config if doesn't exist
if [ ! -f "${CONFIG_DIR}/config.yaml" ]; then
    cp "${INSTALL_DIR}/config/config.yaml.example" "${CONFIG_DIR}/config.yaml"
    echo "Configuration template created at ${CONFIG_DIR}/config.yaml"
    echo "Please edit this file before starting the service!"
fi

# Create MMDVM config directories
mkdir -p /etc/mmdvm
mkdir -p /var/log/mmdvm

echo ""
echo "Step 10: Installing systemd services..."
# Install EasyDispatch service
cp "${INSTALL_DIR}/systemd/easydispatch-collector.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable easydispatch-collector.service

# Create MMDVMHost service if not exists
if [ ! -f "/etc/systemd/system/mmdvmhost.service" ]; then
    cat > /etc/systemd/system/mmdvmhost.service << 'EOF'
[Unit]
Description=MMDVMHost Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/MMDVMHost /etc/mmdvm/MMDVM.ini
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable mmdvmhost.service
fi

echo ""
echo "Step 11: Configuring logrotate..."
cat > /etc/logrotate.d/easydispatch << 'EOF'
/var/log/easydispatch/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 0640 root root
}

/var/log/mmdvm/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 0640 root root
}
EOF

echo ""
echo "Step 12: Setting up firewall (UFW)..."
apt-get install -y ufw
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp  # SSH
ufw allow 62031/udp  # DMRGateway
ufw allow 62032/udp  # MMDVMHost

echo ""
echo "Step 13: Creating utility scripts..."
mkdir -p /usr/local/bin

# Create monitor status script
cat > /usr/local/bin/easydispatch-status << 'EOF'
#!/bin/bash
echo "=== EasyDispatch System Status ==="
echo ""
echo "Services:"
systemctl status mmdvmhost.service --no-pager | head -n 3
systemctl status easydispatch-collector.service --no-pager | head -n 3
echo ""
echo "Recent logs:"
journalctl -u easydispatch-collector.service -n 20 --no-pager
EOF
chmod +x /usr/local/bin/easydispatch-status

# Create backup script
cat > /usr/local/bin/easydispatch-backup << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/lib/easydispatch/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "${BACKUP_DIR}"
tar -czf "${BACKUP_DIR}/easydispatch-config-${TIMESTAMP}.tar.gz" \
    /etc/easydispatch \
    /etc/mmdvm
echo "Backup created: ${BACKUP_DIR}/easydispatch-config-${TIMESTAMP}.tar.gz"
EOF
chmod +x /usr/local/bin/easydispatch-backup

echo ""
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Configure MMDVM frequencies:"
echo "   sudo bash /etc/mmdvm-templates/configure.sh"
echo ""
echo "2. Edit EasyDispatch configuration:"
echo "   sudo nano ${CONFIG_DIR}/config.yaml"
echo ""
echo "3. Start services:"
echo "   sudo systemctl start mmdvmhost"
echo "   sudo systemctl start easydispatch-collector"
echo ""
echo "4. Check status:"
echo "   sudo easydispatch-status"
echo ""
echo "System will reboot in 10 seconds to apply all changes..."
sleep 10
reboot
