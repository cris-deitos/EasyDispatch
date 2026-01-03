#!/bin/bash
# EasyDispatch Configuration Backup Script

BACKUP_DIR="/var/lib/easydispatch/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/easydispatch-backup-${TIMESTAMP}.tar.gz"

echo "=== EasyDispatch Configuration Backup ==="
echo ""

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Create backup
echo "Creating backup..."
tar -czf "${BACKUP_FILE}" \
    /etc/easydispatch \
    /etc/mmdvm \
    /var/lib/easydispatch/offline_queue.json 2>/dev/null || true

if [ -f "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "Backup created successfully!"
    echo "  File: ${BACKUP_FILE}"
    echo "  Size: ${SIZE}"
    echo ""
    
    # Clean up old backups (keep last 10)
    echo "Cleaning up old backups..."
    cd "${BACKUP_DIR}"
    ls -t easydispatch-backup-*.tar.gz | tail -n +11 | xargs rm -f 2>/dev/null || true
    
    REMAINING=$(ls -1 easydispatch-backup-*.tar.gz 2>/dev/null | wc -l)
    echo "Backups retained: ${REMAINING}"
else
    echo "Error: Backup failed!"
    exit 1
fi

echo ""
echo "To restore from backup:"
echo "  tar -xzf ${BACKUP_FILE} -C /"
