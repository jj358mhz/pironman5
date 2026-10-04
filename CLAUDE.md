# Pironman5 Development Guide

## Branches

| Branch | Purpose | Notes |
|--------|---------|-------|
| `ups` | Development mainline | All variants: ups, promax, pipower5 |
| `pipower5` | PiPower5 standalone release | Sync from ups periodically |
| `promax` | Pironman 5 Pro Max release | Sync from ups periodically |

## Architecture

```
pironman5
  ├── PMAuto (pm_auto)
  │   ├── SystemAddon     CPU/RAM/storage/IP
  │   ├── FanAddon        PWM/GPIO fan control
  │   ├── OLEDAddon       Display pages, sleep/wake
  │   ├── PiPower5Addon   UPS battery, buzzer, events
  │   ├── WS2812Addon     RGB LED strip
  │   └── ...
  └── PMDashboard (web UI, port 34001)

piPower5
  ├── kernel driver       sysfs at /sys/class/pipower5/pipower5/
  ├── Python library      pipower5 CLI + email
  └── udev rules          event → systemd-run → email
```

## Variants (products.py)

Variants are assembled from modules (variants/modules/*.py). Each module registers peripherals, default config, event mappings.

| Variant | Modules |
|---------|---------|
| ups | core, network_info, history, oled, oled_ups_pages, pwm_fan, sf_rgb_led, pipower5 |
| pipower5 | core, network_info, history, pipower5 |
| promax | core, network_info, history, oled, ws2812, pi5_power_button |
| nas | core, network_info, oled, pwm_fan, pironman_mcu, rtl8125 |

## Install Script (install.sh)

Uses sunfounder-installer framework. Variants installed via:
```bash
curl .../ups/install.sh | bash -s -- --variant <name>
```

PiPower5 standalone reuses pironman5 framework:
- Variant `pipower5` → installs pironman5 + pipower5 plugin
- Detects and removes old `/opt/pipower5/` installation

## Testing

Test devices:
- `raspberrypi-scanner` — base variant

```bash
# Deploy to test device (this fork's v1 branch)
sudo /opt/pironman5/venv/bin/pip3 install --force-reinstall --no-cache-dir \
  git+https://github.com/jj358mhz/pironman5.git@v1
sudo systemctl restart pironman5

# Always follow a restart with doctor --fix: something in pm_auto/
# pm_dashboard spawns its own influxd under pironman5.service (root),
# which re-breaks /var/lib/influxdb ownership and the influxdb.service
# unit on every restart. This is an upstream behavior, not something
# fixed in this repo - see bin/pironman5.service's comment.
sudo /opt/pironman5/venv/bin/pironman5 doctor --fix

# Check peripherals
curl -s http://localhost:34001/api/v1.0/get-device-info
