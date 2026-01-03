# MMDVM Display Setup Guide

This guide covers the setup and configuration of the OLED/LCD display for EasyDispatch status monitoring on your MMDVM Raspberry Pi.

## Overview

The EasyDispatch collector includes a display manager that shows real-time status information on an OLED display (typically SSD1306 128x64 pixels) connected to the Raspberry Pi via I2C.

### Display Information

The display shows:

1. **Slot Status**
   - `S1:OK` or `S1:No` - Slot 1 receive status
   - `S2:OK` or `S2:No` - Slot 2 receive status

2. **Connection Status**
   - `DB:OK` or `DB:No` - Database connection status
   - `API:OK` or `API:No` - API connection status

3. **DMR Data**
   - Real-time display of received DMR transmissions
   - Shows radio ID, talkgroup, slot, and other relevant data
   - Scrollable text for longer messages

## Hardware Requirements

### Recommended Display

- **SSD1306 OLED Display** - 128x64 pixels, I2C interface
- Available from most electronics suppliers
- Usually operates at 3.3V or 5V

### Connection

The display connects to the Raspberry Pi via I2C:

```
Display Pin    Raspberry Pi Pin
-----------    ----------------
VCC            3.3V (Pin 1 or 17)
GND            Ground (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
SCL            GPIO 3 (SCL) - Pin 5
SDA            GPIO 2 (SDA) - Pin 3
```

## Software Setup

### 1. Enable I2C on Raspberry Pi

```bash
sudo raspi-config
```

Navigate to:
- `Interfacing Options` → `I2C` → `Yes`

Reboot the Raspberry Pi:

```bash
sudo reboot
```

### 2. Install Required System Packages

```bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip libfreetype6-dev libjpeg-dev build-essential
sudo apt-get install -y i2c-tools python3-smbus
```

### 3. Verify I2C Connection

After connecting the display, verify it's detected:

```bash
sudo i2cdetect -y 1
```

You should see the display address (usually `0x3C` or `0x3D`):

```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- --
```

### 4. Install Python Display Libraries

The required libraries are included in the EasyDispatch collector requirements:

```bash
cd /opt/easydispatch
sudo pip3 install luma.oled
```

Or install all requirements:

```bash
sudo pip3 install -r requirements.txt
```

## Configuration

Edit the EasyDispatch configuration file:

```bash
sudo nano /etc/easydispatch/config.yaml
```

Add or update the `display` section:

```yaml
display:
  enabled: true          # Set to false to disable display
  i2c_port: 1           # I2C port number (usually 1)
  i2c_address: 0x3C     # I2C address of display (usually 0x3C)
```

### Configuration Options

- **enabled**: `true` or `false` - Enable or disable the display
- **i2c_port**: I2C port number (usually `1` on newer Raspberry Pi models)
- **i2c_address**: I2C address of the display (use `i2cdetect` to find it)

## Usage

Once configured, the display will automatically start showing status information when the EasyDispatch collector starts.

### Display Layout

```
┌────────────────────────────┐
│ S1:OK S2:No                │  ← Slot RX Status
│ DB:OK API:OK               │  ← Connection Status
├────────────────────────────┤
│ RX S1: 2222000 -> TG1      │  ← DMR Data (3 lines)
│ Duration: 5.2s             │
│ BER: 0.5%                  │
└────────────────────────────┘
```

### Status Indicators

#### Slot Status
- **OK**: Slot is currently receiving a transmission
- **No**: Slot is idle (not receiving)

#### Connection Status
- **OK**: Connection is active and healthy
- **No**: Connection is down or unreachable

### DMR Data Display

The display shows real-time information about DMR transmissions:

- **Voice Transmission Start**: `RX S1: 2222000 -> TG1`
- **Voice Transmission End**: `END S1: 5.2s, BER:0.5%`
- **Data Transmission**: `DATA S2: 2222001 -> TG9`
- **Emergency**: `!!! EMERGENCY !!! Slot 1`

## Troubleshooting

### Display Not Working

1. **Check I2C is enabled**:
   ```bash
   lsmod | grep i2c
   ```
   Should show `i2c_bcm2835` and `i2c_dev`

2. **Verify display is detected**:
   ```bash
   sudo i2cdetect -y 1
   ```

3. **Check permissions**:
   ```bash
   sudo usermod -a -G i2c easydispatch
   ```

4. **Check logs**:
   ```bash
   sudo journalctl -u easydispatch-collector -f
   ```

### Wrong I2C Address

If the display doesn't work, try scanning for the correct address:

```bash
sudo i2cdetect -y 1
```

Update the `i2c_address` in the configuration file to match the detected address.

### Display Shows Garbage

This usually indicates a wiring issue or wrong I2C address. Verify:
- All connections are secure
- I2C address matches the detected address
- Display is compatible with SSD1306 driver

### No Status Updates

If the display shows the startup message but doesn't update:
- Check that the collector is receiving DMR traffic
- Verify API and DB connectivity
- Check collector logs for errors

## Disabling the Display

To disable the display without physically disconnecting it:

Edit `/etc/easydispatch/config.yaml`:

```yaml
display:
  enabled: false
```

Restart the collector:

```bash
sudo systemctl restart easydispatch-collector
```

## Advanced Configuration

### Using Different Display Models

The code is designed for SSD1306 OLED displays, but can be adapted for other models. To use a different display:

1. Install the appropriate driver from the `luma` family:
   - `luma.oled` - OLED displays (SSD1306, SSD1309, SSD1322, SSD1325, SSD1327, SSD1331, SSD1351)
   - `luma.lcd` - LCD displays (PCD8544, ST7735, UC1701X, ILI9341)
   - `luma.led_matrix` - LED matrix displays

2. Modify `collector/display_manager.py` to use the correct device class

### Custom Fonts

To use a custom font, modify the font loading in `display_manager.py`:

```python
self.font = ImageFont.truetype('/path/to/your/font.ttf', 10)
```

## References

- [luma.oled Documentation](https://luma-oled.readthedocs.io/)
- [Raspberry Pi I2C Documentation](https://www.raspberrypi.org/documentation/hardware/raspberrypi/i2c.md)
- [I2C Tools](https://i2c.wiki.kernel.org/index.php/I2C_Tools)

## Support

For issues specific to the display functionality:
1. Check the troubleshooting section above
2. Review collector logs: `sudo journalctl -u easydispatch-collector -f`
3. Open an issue on GitHub with:
   - Output of `i2cdetect -y 1`
   - Collector logs
   - Configuration file (with API key redacted)
