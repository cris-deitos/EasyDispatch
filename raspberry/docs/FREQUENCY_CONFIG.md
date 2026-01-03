# EasyDispatch Frequency Configuration Guide

## Overview

EasyDispatch supports **custom VHF and UHF frequencies** without limitations, allowing you to use any frequency within the hardware capabilities of the MMDVM_HS_Dual_Hat.

## Supported Frequency Ranges

### VHF Band
- **Range**: 136-174 MHz
- **Common Uses**:
  - Amateur Radio 2m: 144-148 MHz
  - Commercial VHF: 136-174 MHz
  - Marine VHF: 156-163 MHz

### UHF Band
- **Range**: 400-480 MHz
- **Common Uses**:
  - Amateur Radio 70cm: 430-450 MHz
  - Commercial UHF: 400-480 MHz
  - PMR446: 446 MHz

## Duplex vs Simplex

### Duplex Mode (Recommended for EasyDispatch)
- **RX and TX on different frequencies**
- Allows simultaneous receive and transmit
- Required for repeater operation
- Typical offset: 0.6 MHz (VHF), 5 MHz (UHF)

Example:
```
RX: 433.4500 MHz
TX: 434.4500 MHz
Offset: +1.000 MHz
```

### Simplex Mode
- RX and TX on same frequency
- Used for direct radio-to-radio
- Not recommended for dispatch operations

Example:
```
RX: 433.4500 MHz
TX: 433.4500 MHz
Offset: 0 MHz
```

## Configuration Methods

### Method 1: Interactive Script (Recommended)

Run the configuration script:

```bash
sudo bash /etc/mmdvm-templates/configure.sh
```

Follow the prompts:
1. Enter callsign
2. Enter DMR ID
3. Enter RX frequency
4. Enter TX frequency
5. Enter coordinates and location

The script will:
- Validate input
- Generate configuration files
- Apply settings
- Restart services

### Method 2: Quick Frequency Update

If you only need to change frequencies:

```bash
sudo bash /opt/easydispatch/scripts/update-frequencies.sh
```

This updates frequencies without changing other settings.

### Method 3: Manual Configuration

Edit MMDVM configuration directly:

```bash
sudo nano /etc/mmdvm/MMDVM.ini
```

Find and modify:

```ini
[Info]
RXFrequency=433.4500
TXFrequency=434.4500
```

Restart services:

```bash
sudo systemctl restart mmdvmhost
```

## Frequency Examples

### Amateur Radio VHF (2m)

**Europe (1.6 MHz offset):**
```
RX: 145.2000 MHz
TX: 145.8000 MHz
```

**USA (0.6 MHz offset):**
```
RX: 146.5200 MHz
TX: 147.1200 MHz
```

### Amateur Radio UHF (70cm)

**Europe (7.6 MHz offset):**
```
RX: 438.5000 MHz
TX: 430.9000 MHz
```

**USA (5 MHz offset):**
```
RX: 442.5000 MHz
TX: 447.5000 MHz
```

### Commercial VHF

**Emergency Services:**
```
RX: 164.5000 MHz
TX: 169.5000 MHz
```

**Business Band:**
```
RX: 151.8250 MHz
TX: 156.2450 MHz
```

### Commercial UHF

**Business Band:**
```
RX: 465.0000 MHz
TX: 470.0000 MHz
```

**Public Safety:**
```
RX: 453.0000 MHz
TX: 458.0000 MHz
```

## Calculating Frequency Offset

Offset = TX Frequency - RX Frequency

**Positive offset (TX higher than RX):**
```
RX: 433.4500 MHz
TX: 434.4500 MHz
Offset: +1.0000 MHz
```

**Negative offset (TX lower than RX):**
```
RX: 438.5000 MHz
TX: 430.9000 MHz
Offset: -7.6000 MHz
```

## Color Code Configuration

DMR uses Color Codes (0-15) to prevent interference:

Edit `/etc/mmdvm/MMDVM.ini`:

```ini
[DMR]
ColorCode=1
```

**Guidelines:**
- Use different color codes for nearby systems
- Color Code 1 is common for private systems
- Color Codes 2-15 available for your use
- Must match on all radios in your network

## Power Level Configuration

Adjust TX power to minimize interference:

Edit `/etc/mmdvm/MMDVM.ini`:

```ini
[Modem]
TXLevel=50
```

**Power Levels:**
- 0-100 scale (percentage)
- Start with 50% and adjust as needed
- Higher power = more coverage but more heat
- Lower power = less coverage but cooler operation

**Typical Settings:**
- Short range (< 1 km): 25-40%
- Medium range (1-5 km): 40-60%
- Long range (> 5 km): 60-80%

## Frequency Planning Tips

### 1. Check Local Regulations
- Ensure you have license for frequencies
- Check band plans
- Verify power limits
- Follow duty cycle restrictions

### 2. Avoid Interference
- Research existing users on frequency
- Use spectrum analyzer if available
- Monitor before transmitting
- Choose quiet frequencies

### 3. Coordination
- Coordinate with other users in area
- Join local frequency coordination groups
- Register your frequencies if required
- Use proper etiquette

### 4. Testing
- Start with low power
- Test RX and TX separately
- Verify coverage area
- Check for interference

## Frequency Validation

The configuration script validates:

1. **Format**: Must be decimal (e.g., 433.4500)
2. **Range**: Within hardware limits (136-174 or 400-480 MHz)
3. **Precision**: Up to 4 decimal places supported

**Invalid examples:**
```
433,4500  ❌ (comma instead of period)
433       ❌ (missing decimal)
500.0000  ❌ (out of range)
```

**Valid examples:**
```
433.4500  ✓
144.8000  ✓
465.0125  ✓
```

## Advanced: Frequency Shifting

For advanced users, you can fine-tune with RX/TX offset:

Edit `/etc/mmdvm/MMDVM.ini`:

```ini
[Modem]
RXOffset=0
TXOffset=0
```

Values in Hz:
- Positive: Shift up
- Negative: Shift down
- Range: -1000 to +1000 Hz

Use for fine frequency correction if needed.

## Troubleshooting Frequency Issues

### Poor Reception

1. **Check antenna**
   - Verify antenna is for correct band
   - Check connections
   - Measure VSWR if possible

2. **Check frequency**
   - Verify RX frequency is correct
   - Check for nearby interference
   - Try different frequency

3. **Check RX sensitivity**
   ```ini
   [Modem]
   RXLevel=50
   ```
   Try values 40-60

### Cannot Transmit

1. **Check license**
   - Verify you can transmit on frequency
   - Check power limits

2. **Check TX frequency**
   - Verify TX frequency is correct
   - Check it's within band limits

3. **Check TX power**
   ```ini
   [Modem]
   TXLevel=50
   ```
   Start low and increase

### Frequency Drift

Temperature can affect frequency stability:

1. **Allow warm-up time**
   - Let system run for 10-15 minutes
   - Frequency stabilizes with temperature

2. **Improve cooling**
   - Add heatsinks
   - Improve ventilation
   - Add fan

3. **Calibrate if needed**
   ```ini
   [Modem]
   RXOffset=100  # Example: +100 Hz
   TXOffset=-50  # Example: -50 Hz
   ```

## Spectrum Analysis

To analyze your frequency before use:

```bash
# Install rtl-sdr tools
sudo apt-get install rtl-sdr

# Scan frequency range (requires RTL-SDR dongle)
rtl_power -f 433M:434M:1k -i 1 scan.csv

# Visualize (requires additional tools)
```

Or use dedicated spectrum analyzer hardware.

## Frequency Bands by Country

### Italy
- VHF: 144-146 MHz (Amateur)
- UHF: 430-434, 434-438 MHz (Amateur)
- PMR446: 446.00625-446.19375 MHz

### USA
- VHF: 144-148 MHz (Amateur)
- UHF: 420-450 MHz (Amateur)
- GMRS: 462-467 MHz

### UK
- VHF: 144-146 MHz (Amateur)
- UHF: 430-440 MHz (Amateur)

### Germany
- VHF: 144-146 MHz (Amateur)
- UHF: 430-440 MHz (Amateur)

**Always verify current regulations for your country!**

## Resources

- **Frequency Allocations**: Check your national frequency allocation table
- **Band Plans**: IARU band plans for amateur frequencies
- **Coordination**: Local frequency coordination groups
- **Calculators**: Online frequency calculators and converters

## Safety and Legal

⚠️ **Important:**
- **Always** ensure you have proper authorization for frequencies used
- **Never** transmit on emergency/public safety frequencies without authorization
- **Follow** local power and duty cycle limits
- **Register** frequencies if required in your jurisdiction
- **Monitor** before transmitting
- **Use** proper identification (callsign) when required

## Next Steps

1. Plan your frequency allocation
2. Verify licenses and authorizations
3. Configure using one of the methods above
4. Test with low power
5. Verify coverage and performance
6. Document your configuration
7. Train users on proper frequencies

## Support

For frequency-related questions:
- Check your national frequency authority website
- Consult local amateur radio clubs
- Join DMR user groups
- See GitHub Issues: https://github.com/cris-deitos/EasyDispatch/issues
