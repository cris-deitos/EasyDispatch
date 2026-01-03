#!/bin/bash
# EasyDispatch First Boot Setup Script
# Runs on first boot to configure the Raspberry Pi

set -e

LOG_FILE="/var/log/easydispatch-firstboot.log"
MARKER_FILE="/var/lib/easydispatch/firstboot-done"

exec > >(tee -a "${LOG_FILE}") 2>&1

echo "=== EasyDispatch First Boot Setup - $(date) ==="

# Update package list
echo "Updating package lists..."
apt-get update

# Install packages from list
echo "Installing required packages..."
if [ -f "/usr/local/share/easydispatch-packages.txt" ]; then
    grep -v '^#' /usr/local/share/easydispatch-packages.txt | grep -v '^$' | xargs apt-get install -y
fi

# Install Python packages
echo "Installing Python packages..."
pip3 install --upgrade pip
pip3 install PyYAML requests pyserial

# Configure I2C for OLED display
echo "Enabling I2C..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" >> /boot/config.txt
fi

# Load I2C kernel module
modprobe i2c-dev
echo "i2c-dev" >> /etc/modules

# Configure UART for MMDVM
echo "Configuring UART..."
systemctl disable hciuart 2>/dev/null || true
systemctl stop serial-getty@ttyAMA0.service 2>/dev/null || true
systemctl disable serial-getty@ttyAMA0.service 2>/dev/null || true

# Create EasyDispatch directories
echo "Creating EasyDispatch directories..."
mkdir -p /etc/easydispatch
mkdir -p /var/log/easydispatch
mkdir -p /var/lib/easydispatch
mkdir -p /opt/easydispatch

# Set permissions
chown -R root:root /etc/easydispatch
chmod 755 /etc/easydispatch
chmod 755 /var/log/easydispatch
chmod 755 /var/lib/easydispatch

# Configure logrotate
echo "Configuring log rotation..."
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
EOF

# Expand filesystem
echo "Expanding filesystem..."
raspi-config nonint do_expand_rootfs

# Set timezone to Europe/Rome (default for Italian dispatch)
echo "Setting timezone..."
timedatectl set-timezone Europe/Rome

# Enable NTP
timedatectl set-ntp true

# Configure hostname
HOSTNAME="easydispatch-$(cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2 | tail -c 9)"
echo "Setting hostname to ${HOSTNAME}..."
hostnamectl set-hostname "${HOSTNAME}"

# Create marker file to prevent re-running
mkdir -p "$(dirname "${MARKER_FILE}")"
touch "${MARKER_FILE}"

echo "=== First Boot Setup Complete ==="
echo "System will reboot in 10 seconds..."
sleep 10
reboot
