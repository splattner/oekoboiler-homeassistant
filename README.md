# Oekoboiler Integration for HomeAssistant

Custom Home Assistant integration that reads OekoBoiler display values from a camera image.

## Features

- Sensors for mode, state, set temperature, water temperature, and level
- Processed debug camera image with OCR boundary overlays
- Config flow with camera entity selector
- Runtime options for OCR boundaries and thresholds

## Installation

1. Copy `custom_components/oekoboiler` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration from **Settings → Devices & Services → Add Integration**.
4. Select the camera entity that points to your OekoBoiler display.

## Options

- Boundary values use format: `x1, y1, x2, y2`
- Illumination threshold range: `1-100`
- Gray threshold range: `0-255`

If OCR values look wrong, tune boundaries first, then thresholds.