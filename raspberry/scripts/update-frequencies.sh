#!/bin/bash
# Update MMDVM Frequencies Script
# Quick script to update frequencies without full reconfiguration

set -e

MMDVM_CONFIG="/etc/mmdvm/MMDVM.ini"

echo "=== EasyDispatch Frequency Update ==="
echo ""

if [ ! -f "${MMDVM_CONFIG}" ]; then
    echo "Error: MMDVM configuration not found at ${MMDVM_CONFIG}"
    echo "Please run configure.sh first!"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

# Show current frequencies
echo "Current frequencies:"
grep "^RXFrequency=" "${MMDVM_CONFIG}" || echo "  RX: Not set"
grep "^TXFrequency=" "${MMDVM_CONFIG}" || echo "  TX: Not set"
echo ""

# Read new frequencies
read -p "New RX Frequency (MHz, e.g., 433.4500): " RX_FREQ
while ! [[ "$RX_FREQ" =~ ^[0-9]+\.[0-9]+$ ]]; do
    echo "Invalid frequency format. Use format: 433.4500"
    read -p "New RX Frequency (MHz): " RX_FREQ
done

read -p "New TX Frequency (MHz, e.g., 434.4500): " TX_FREQ
while ! [[ "$TX_FREQ" =~ ^[0-9]+\.[0-9]+$ ]]; do
    echo "Invalid frequency format. Use format: 434.4500"
    read -p "New TX Frequency (MHz): " TX_FREQ
done

echo ""
echo "New frequencies:"
echo "  RX: ${RX_FREQ} MHz"
echo "  TX: ${TX_FREQ} MHz"
echo ""

read -p "Apply these frequencies? (Y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Backup current config
cp "${MMDVM_CONFIG}" "${MMDVM_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

# Update frequencies
sed -i "s/^RXFrequency=.*/RXFrequency=${RX_FREQ}/" "${MMDVM_CONFIG}"
sed -i "s/^TXFrequency=.*/TXFrequency=${TX_FREQ}/" "${MMDVM_CONFIG}"

echo "Frequencies updated!"
echo ""
echo "Restarting MMDVM services..."
systemctl restart mmdvmhost
systemctl restart dmrgateway 2>/dev/null || true

echo ""
echo "Done! New frequencies are active."
echo ""
echo "Verify with: grep Frequency ${MMDVM_CONFIG}"
