# EasyDispatch Hardware Setup Guide

## Required Hardware

### Main Components

1. **Raspberry Pi 3 Model B v1.2**
   - Quad-core ARM Cortex-A53 processor
   - 1GB RAM
   - MicroSD card (minimum 16GB, recommended 32GB Class 10)
   - 5V 2.5A power supply

2. **MMDVM_HS_Dual_Hat**
   - KiCad MMDVM_HS_Dual_Hat Duplex MMDVM Hotspot
   - Supports UHF/VHF
   - Protocols: P25, DMR, YSF, NXDN
   - Integrated OLED display (128x64)

3. **Antenna**
   - Dual-band UHF/VHF antenna
   - SMA connector
   - Appropriate for your frequency range

### Additional Components

- Heatsinks for Raspberry Pi (recommended)
- Case for Raspberry Pi + MMDVM Hat (recommended)
- Ethernet cable or WiFi dongle (if not using built-in WiFi)

## Hardware Assembly

### Step 1: Prepare Raspberry Pi

1. Install heatsinks on Raspberry Pi CPU and other chips
2. Ensure Raspberry Pi is on a non-conductive surface

### Step 2: Install MMDVM_HS_Dual_Hat

1. **IMPORTANT**: Ensure Raspberry Pi is powered OFF

2. Align the MMDVM_HS_Dual_Hat with the GPIO header (40-pin)
   ```
   Pin alignment:
   - Hat covers all 40 GPIO pins
   - Ensure proper alignment before pressing down
   ```

3. Gently press the hat down onto the GPIO header
   - Apply even pressure
   - Ensure all pins are fully inserted

4. The OLED display should be visible on top of the hat

### Step 3: Jumper Configuration

The MMDVM_HS_Dual_Hat requires specific jumper settings for Raspberry Pi:

**Required Jumper Settings:**

```
Jumper Position    Setting
----------------------------------
J1 (PTT)           Open (no jumper)
J2 (COS)           Open (no jumper)  
J3 (MODE)          Pins 2-3 (Duplex mode)
```

**Mode Selection (J3):**
- Pins 1-2: Simplex mode
- Pins 2-3: Duplex mode (REQUIRED for EasyDispatch)

### Step 4: Connect Antenna

1. Connect your UHF/VHF antenna to the SMA connector on the hat
2. **NEVER** operate without antenna - this can damage the transmitter!
3. Ensure antenna is appropriate for your frequency range

### Step 5: Power Connection

1. Connect the power supply to Raspberry Pi
2. **Do NOT power on yet** - complete software installation first

## Hardware Verification

Before powering on, verify:

- [ ] MMDVM Hat is firmly seated on GPIO pins
- [ ] Jumpers are in correct positions
- [ ] Antenna is connected
- [ ] Power supply is 5V 2.5A minimum
- [ ] All connections are secure

## UART Configuration

The MMDVM Hat uses the Raspberry Pi's hardware UART (serial port):

- **Device**: `/dev/ttyAMA0`
- **Speed**: 115200 baud
- **Bluetooth**: Must be disabled (handled by installation script)

## I2C Configuration (OLED Display)

The OLED display uses I2C:

- **Bus**: I2C-1
- **Address**: 0x3C (default)
- **Resolution**: 128x64 pixels

## Frequency Ranges

The MMDVM_HS_Dual_Hat supports:

**VHF:**
- 136-174 MHz
- Typical: 144-148 MHz (Amateur 2m band)

**UHF:**
- 400-480 MHz
- Typical: 430-450 MHz (Amateur 70cm band)

**EasyDispatch supports CUSTOM frequencies:**
- Any frequency within the hardware range
- Configure during setup via `configure.sh`

## Power Consumption

Typical power consumption:
- Idle: ~500mA (2.5W)
- Receiving: ~600mA (3W)
- Transmitting: ~800-1200mA (4-6W)

Ensure your power supply can handle peak load.

## Heat Management

The MMDVM Hat's RF amplifier generates heat:

- Use heatsinks (included with some versions)
- Ensure adequate ventilation
- Consider a case with fan for continuous operation
- Monitor temperature: `vcgencmd measure_temp`

## LED Indicators

The MMDVM Hat has LED indicators:

- **Power LED**: Green - indicates power
- **Status LED**: Red - indicates PTT (transmitting)
- **Activity LED**: Yellow - indicates activity

## Troubleshooting Hardware

### OLED Display Not Working

1. Check I2C is enabled: `sudo raspi-config` → Interface Options → I2C
2. Verify I2C device: `i2cdetect -y 1` (should show 0x3C)
3. Check cable connections

### No Serial Communication

1. Verify UART is enabled in `/boot/config.txt`:
   ```
   enable_uart=1
   dtoverlay=pi3-disable-bt
   ```
2. Check device exists: `ls -l /dev/ttyAMA0`
3. Verify no other process is using UART

### Poor RF Performance

1. Check antenna connection
2. Verify antenna is appropriate for frequency
3. Check VSWR if possible
4. Ensure antenna is properly grounded
5. Check for RF interference

### Overheating

1. Add or upgrade heatsinks
2. Improve ventilation
3. Reduce TX power in MMDVM.ini
4. Add a fan

## Safety Warnings

⚠️ **RF Safety:**
- Never operate without antenna
- Keep antenna away from people during transmission
- Follow local RF exposure guidelines

⚠️ **Electrical Safety:**
- Always power off before connecting/disconnecting components
- Use only specified power supply
- Avoid short circuits

⚠️ **Regulatory Compliance:**
- Ensure you have proper license for frequencies used
- Follow local regulations for RF transmission
- Some frequencies require specific certifications

## Next Steps

After hardware assembly:

1. Follow [INSTALLATION.md](INSTALLATION.md) for software setup
2. Configure frequencies in [FREQUENCY_CONFIG.md](FREQUENCY_CONFIG.md)
3. Test system with low power before full operation
