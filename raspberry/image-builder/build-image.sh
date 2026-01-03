#!/bin/bash
# EasyDispatch - Raspberry Pi Image Builder Script
# This script creates a custom Raspberry Pi OS image with all necessary components

set -e

# Configuration
RPI_OS_IMAGE_URL="https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2023-12-11/2023-12-11-raspios-bookworm-armhf-lite.img.xz"
IMAGE_NAME="easydispatch-$(date +%Y%m%d).img"
WORK_DIR="/tmp/easydispatch-build"
MOUNT_POINT="${WORK_DIR}/mount"

echo "=== EasyDispatch Image Builder ==="
echo "Building custom Raspberry Pi OS image..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

# Create working directory
mkdir -p "${WORK_DIR}"
mkdir -p "${MOUNT_POINT}"

# Download base image
echo "Downloading Raspberry Pi OS Lite..."
cd "${WORK_DIR}"
if [ ! -f "base-image.img.xz" ]; then
    wget -O base-image.img.xz "${RPI_OS_IMAGE_URL}"
fi

# Extract image
echo "Extracting image..."
if [ ! -f "base-image.img" ]; then
    xz -d -k base-image.img.xz
fi

# Copy to working image
cp base-image.img "${IMAGE_NAME}"

# Get partition offsets
echo "Mounting image..."
BOOT_OFFSET=$(fdisk -l "${IMAGE_NAME}" | grep "^${IMAGE_NAME}1" | awk '{print $2}')
ROOT_OFFSET=$(fdisk -l "${IMAGE_NAME}" | grep "^${IMAGE_NAME}2" | awk '{print $2}')

BOOT_OFFSET=$((BOOT_OFFSET * 512))
ROOT_OFFSET=$((ROOT_OFFSET * 512))

# Mount root partition
mkdir -p "${MOUNT_POINT}/root"
mount -o loop,offset=${ROOT_OFFSET} "${IMAGE_NAME}" "${MOUNT_POINT}/root"

# Mount boot partition
mkdir -p "${MOUNT_POINT}/boot"
mount -o loop,offset=${BOOT_OFFSET} "${IMAGE_NAME}" "${MOUNT_POINT}/boot"

# Copy firstboot script
echo "Installing firstboot script..."
cp "$(dirname "$0")/firstboot.sh" "${MOUNT_POINT}/root/usr/local/bin/easydispatch-firstboot.sh"
chmod +x "${MOUNT_POINT}/root/usr/local/bin/easydispatch-firstboot.sh"

# Create systemd service for firstboot
cat > "${MOUNT_POINT}/root/etc/systemd/system/easydispatch-firstboot.service" << 'EOF'
[Unit]
Description=EasyDispatch First Boot Setup
After=network.target
ConditionPathExists=!/var/lib/easydispatch/firstboot-done

[Service]
Type=oneshot
ExecStart=/usr/local/bin/easydispatch-firstboot.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable firstboot service
chroot "${MOUNT_POINT}/root" systemctl enable easydispatch-firstboot.service

# Configure boot options for MMDVM Hat
echo "Configuring boot options for MMDVM Hat..."
cat >> "${MOUNT_POINT}/boot/config.txt" << 'EOF'

# EasyDispatch MMDVM_HS_Dual_Hat Configuration
dtoverlay=pi3-disable-bt
enable_uart=1
dtoverlay=mmdvm-hs-dual-hat
force_turbo=0
EOF

# Create packages list reference
cp "$(dirname "$0")/packages.txt" "${MOUNT_POINT}/root/usr/local/share/easydispatch-packages.txt"

# Enable SSH
touch "${MOUNT_POINT}/boot/ssh"

# Unmount
echo "Unmounting image..."
sync
umount "${MOUNT_POINT}/boot"
umount "${MOUNT_POINT}/root"

# Compress final image
echo "Compressing final image..."
xz -z -k "${IMAGE_NAME}"

echo "=== Build Complete ==="
echo "Image created: ${WORK_DIR}/${IMAGE_NAME}.xz"
echo ""
echo "To write to SD card:"
echo "  xzcat ${IMAGE_NAME}.xz | sudo dd of=/dev/sdX bs=4M status=progress"
echo ""
echo "Replace /dev/sdX with your SD card device"
