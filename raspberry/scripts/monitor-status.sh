#!/bin/bash
# EasyDispatch System Status Monitor Script

echo "========================================"
echo "    EasyDispatch System Status"
echo "========================================"
echo ""

# System Info
echo "=== System Information ==="
hostname
uptime
echo ""

# Service Status
echo "=== Service Status ==="
echo ""
echo "MMDVMHost:"
systemctl is-active mmdvmhost.service && echo "  ✓ Running" || echo "  ✗ Stopped"
echo ""
echo "EasyDispatch Collector:"
systemctl is-active easydispatch-collector.service && echo "  ✓ Running" || echo "  ✗ Stopped"
echo ""

# Configuration
echo "=== Configuration ==="
if [ -f "/etc/mmdvm/MMDVM.ini" ]; then
    echo "MMDVM Frequencies:"
    grep "^RXFrequency=" /etc/mmdvm/MMDVM.ini | sed 's/RXFrequency=/  RX: /' || echo "  RX: Not configured"
    grep "^TXFrequency=" /etc/mmdvm/MMDVM.ini | sed 's/TXFrequency=/  TX: /' || echo "  TX: Not configured"
    echo ""
    echo "DMR ID:"
    grep "^Id=" /etc/mmdvm/MMDVM.ini | sed 's/Id=/  /' || echo "  Not configured"
    echo ""
    echo "Callsign:"
    grep "^Callsign=" /etc/mmdvm/MMDVM.ini | sed 's/Callsign=/  /' || echo "  Not configured"
else
    echo "  ✗ MMDVM not configured"
fi
echo ""

# Recent Activity
echo "=== Recent Activity (last 10 log entries) ==="
if systemctl is-active easydispatch-collector.service >/dev/null 2>&1; then
    journalctl -u easydispatch-collector.service -n 10 --no-pager | tail -n 10
else
    echo "  Service not running"
fi
echo ""

# Disk Space
echo "=== Disk Space ==="
df -h / | tail -n 1 | awk '{print "  Used: " $3 " / " $2 " (" $5 ")"}'
echo ""

# Audio Files
echo "=== Audio Files ==="
if [ -d "/var/lib/easydispatch/audio" ]; then
    FILE_COUNT=$(ls -1 /var/lib/easydispatch/audio 2>/dev/null | wc -l)
    if [ $FILE_COUNT -gt 0 ]; then
        TOTAL_SIZE=$(du -sh /var/lib/easydispatch/audio 2>/dev/null | cut -f1)
        echo "  Files: ${FILE_COUNT}"
        echo "  Total size: ${TOTAL_SIZE}"
    else
        echo "  No audio files"
    fi
else
    echo "  Audio directory not found"
fi
echo ""

# Network Status
echo "=== Network Status ==="
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "  ✓ Internet connection OK"
else
    echo "  ✗ No internet connection"
fi
echo ""

# API Status
if [ -f "/etc/easydispatch/config.yaml" ]; then
    API_ENDPOINT=$(grep "endpoint:" /etc/easydispatch/config.yaml | awk '{print $2}' | tr -d '"')
    if [ ! -z "$API_ENDPOINT" ]; then
        echo "  API Endpoint: ${API_ENDPOINT}"
        # Try to ping the API (simplified)
        API_HOST=$(echo "$API_ENDPOINT" | sed 's|https\?://||' | cut -d'/' -f1)
        if ping -c 1 "$API_HOST" >/dev/null 2>&1; then
            echo "  ✓ API host reachable"
        else
            echo "  ✗ API host unreachable"
        fi
    fi
fi
echo ""

echo "========================================"
echo "For detailed logs: journalctl -u easydispatch-collector.service -f"
echo "For MMDVM logs: tail -f /var/log/mmdvm/MMDVM.log"
echo "========================================"
