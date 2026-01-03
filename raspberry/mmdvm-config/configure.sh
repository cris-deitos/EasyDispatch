#!/bin/bash
# EasyDispatch MMDVM Configuration Script
# Interactive script to configure custom frequencies and parameters

set -e

CONFIG_DIR="/etc/mmdvm"
TEMPLATE_DIR="$(dirname "$0")"
MMDVM_TEMPLATE="${TEMPLATE_DIR}/MMDVM.ini.template"
GATEWAY_TEMPLATE="${TEMPLATE_DIR}/DMRGateway.ini.template"
MMDVM_CONFIG="${CONFIG_DIR}/MMDVM.ini"
GATEWAY_CONFIG="${CONFIG_DIR}/DMRGateway.ini"

echo "=== EasyDispatch MMDVM Configuration ==="
echo ""

# Create config directory if it doesn't exist
mkdir -p "${CONFIG_DIR}"

# Check if templates exist
if [ ! -f "${MMDVM_TEMPLATE}" ]; then
    echo "Error: MMDVM.ini.template not found!"
    exit 1
fi

if [ ! -f "${GATEWAY_TEMPLATE}" ]; then
    echo "Error: DMRGateway.ini.template not found!"
    exit 1
fi

# Read current configuration if exists
if [ -f "${MMDVM_CONFIG}" ]; then
    echo "Existing configuration found."
    read -p "Do you want to reconfigure? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo ""
echo "Please provide the following information:"
echo ""

# Callsign
read -p "Callsign: " CALLSIGN
CALLSIGN=${CALLSIGN^^}  # Convert to uppercase

# DMR ID
read -p "DMR ID: " DMR_ID
while ! [[ "$DMR_ID" =~ ^[0-9]+$ ]]; do
    echo "Invalid DMR ID. Must be numeric."
    read -p "DMR ID: " DMR_ID
done

# RX Frequency
read -p "RX Frequency (MHz, e.g., 433.4500): " RX_FREQ
while ! [[ "$RX_FREQ" =~ ^[0-9]+\.[0-9]+$ ]]; do
    echo "Invalid frequency format. Use format: 433.4500"
    read -p "RX Frequency (MHz): " RX_FREQ
done

# TX Frequency
read -p "TX Frequency (MHz, e.g., 434.4500): " TX_FREQ
while ! [[ "$TX_FREQ" =~ ^[0-9]+\.[0-9]+$ ]]; do
    echo "Invalid frequency format. Use format: 434.4500"
    read -p "TX Frequency (MHz): " TX_FREQ
done

# Latitude
read -p "Latitude (decimal, e.g., 45.464664): " LATITUDE
while ! [[ "$LATITUDE" =~ ^-?[0-9]+\.[0-9]+$ ]]; do
    echo "Invalid latitude format. Use decimal format: 45.464664"
    read -p "Latitude: " LATITUDE
done

# Longitude
read -p "Longitude (decimal, e.g., 9.188540): " LONGITUDE
while ! [[ "$LONGITUDE" =~ ^-?[0-9]+\.[0-9]+$ ]]; do
    echo "Invalid longitude format. Use decimal format: 9.188540"
    read -p "Longitude: " LONGITUDE
done

# Location
read -p "Location (e.g., Milano, IT): " LOCATION

echo ""
echo "Configuration Summary:"
echo "  Callsign: ${CALLSIGN}"
echo "  DMR ID: ${DMR_ID}"
echo "  RX Frequency: ${RX_FREQ} MHz"
echo "  TX Frequency: ${TX_FREQ} MHz"
echo "  Latitude: ${LATITUDE}"
echo "  Longitude: ${LONGITUDE}"
echo "  Location: ${LOCATION}"
echo ""

read -p "Is this correct? (Y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Configuration cancelled."
    exit 0
fi

# Generate MMDVM.ini
echo "Generating MMDVM.ini..."
sed -e "s/{{CALLSIGN}}/${CALLSIGN}/g" \
    -e "s/{{DMR_ID}}/${DMR_ID}/g" \
    -e "s/{{RX_FREQ}}/${RX_FREQ}/g" \
    -e "s/{{TX_FREQ}}/${TX_FREQ}/g" \
    -e "s/{{LATITUDE}}/${LATITUDE}/g" \
    -e "s/{{LONGITUDE}}/${LONGITUDE}/g" \
    -e "s/{{LOCATION}}/${LOCATION}/g" \
    "${MMDVM_TEMPLATE}" > "${MMDVM_CONFIG}"

# Generate DMRGateway.ini
echo "Generating DMRGateway.ini..."
sed -e "s/{{CALLSIGN}}/${CALLSIGN}/g" \
    -e "s/{{DMR_ID}}/${DMR_ID}/g" \
    -e "s/{{LATITUDE}}/${LATITUDE}/g" \
    -e "s/{{LONGITUDE}}/${LONGITUDE}/g" \
    -e "s/{{LOCATION}}/${LOCATION}/g" \
    "${GATEWAY_TEMPLATE}" > "${GATEWAY_CONFIG}"

# Validate configuration
echo "Validating configuration..."

# Check frequency range
RX_FREQ_INT=$(echo "$RX_FREQ" | cut -d'.' -f1)
TX_FREQ_INT=$(echo "$TX_FREQ" | cut -d'.' -f1)

if [ $RX_FREQ_INT -lt 130 ] || [ $RX_FREQ_INT -gt 1300 ]; then
    echo "Warning: RX frequency is outside typical range (130-1300 MHz)"
fi

if [ $TX_FREQ_INT -lt 130 ] || [ $TX_FREQ_INT -gt 1300 ]; then
    echo "Warning: TX frequency is outside typical range (130-1300 MHz)"
fi

# Set permissions
chmod 644 "${MMDVM_CONFIG}"
chmod 644 "${GATEWAY_CONFIG}"

echo ""
echo "Configuration complete!"
echo ""
echo "Configuration files created:"
echo "  ${MMDVM_CONFIG}"
echo "  ${GATEWAY_CONFIG}"
echo ""
echo "To apply changes, restart MMDVM services:"
echo "  sudo systemctl restart mmdvmhost"
echo "  sudo systemctl restart dmrgateway"
echo ""
