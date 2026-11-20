# Xiaomi Mi Band 5 watch face hardware guide

This document records the hardware rules, firmware constraints, and binary packing requirements discovered while building and debugging watch faces on the physical Xiaomi Mi Band 5 (display controller model `miband5`, `UIHH_MIBAND`).

## Hardware specifications

The band display has the following specifications:

- Resolution: 126 pixels wide by 294 pixels high (126x294).
- Panel: AMOLED color display with rounded top and bottom capsule edges.
- Color depth: 16-bit high color.
- File format: Packed binary `.bin` container containing a header, Protobuf metadata, and bitmap image chunks.

## Critical hardware constraints

### 1. 4KB hardware blitter buffer limit

The Mi Band 5 display blitter has a hard buffer limit of 4096 bytes per sprite. If any individual sprite exceeds 4096 bytes, the display blitter crashes or silently drops the element.

For 8bpp indexed images (`0x64` format):

```
Buffer size = 16 bytes (header) + 1024 bytes (palette) + (width * height) bytes
```

Because `16 + 1024 = 1040` bytes are reserved for the header and palette:

```
Maximum sprite area = 4096 - 1040 = 3056 pixels
```

Any sprite where `width * height > 3056` fails hardware rendering.

Examples:
- Font size 80 with bounding box 44x65: area is 2860 pixels (buffer size 3900 bytes). This fits within the 4096-byte limit and renders safely.
- Font size 84 with bounding box 46x68: area is 3128 pixels (buffer size 4168 bytes). This exceeds 4096 bytes and crashes the display engine.

### 2. Indexed color format requirement (0x64)

The watch face engine requires sprites to use 8bpp indexed color mode (`0x64`).

The packing tool `watchface-js` inspects alpha values in PNG sprites:
- If a sprite contains only binary alpha (pixels are either fully transparent with alpha 0, or fully opaque with alpha 255), the packer stores it as `0x64` (8bpp indexed).
- If a sprite contains intermediate alpha values (1 through 254), the packer cannot build an indexed table and falls back to `0x1B` (uncompressed 24-bit raw RGB).

Raw `0x1B` sprites fail to render on the band blitter. All sprites except the full-screen background and the preview image must have strict binary alpha (0 or 255).

### 3. Font rasterization and alpha thresholding

When TrueType or WOFF2 fonts are rasterized onto small pixel grids with Pillow or FreeType, subpixel anti-aliasing spreads thin strokes across neighboring scanlines with partial alpha.

If you apply a naive binarization threshold such as `alpha >= 128`:
- Scanlines with alpha around 110 to 125 are deleted.
- Thin horizontal strokes (such as the top arch of 6, the top bar of 5, and the top curve of 0) disappear.
- The digits look cut off or incomplete on the OLED screen.

To fix this:
1. Snap the render position to integer coordinates: `tx = int(...)` and `ty = int(...)`.
2. Use a binarization threshold of 100 (`alpha.point(lambda p: 255 if p >= 100 else 0)`).
3. Verify that the top and bottom strokes have equal pixel thickness before packaging.

### 4. Mandatory Protobuf tags

The Mi Band 5 firmware expects specific Protobuf tags in the parsed `watchface.json` file:

- `Time.DrawingOrder`: Must be `false` (Protobuf tag 11). If missing or `true`, time digits fail to display.
- `Activity.UnknownV7`: Must be `0` (Protobuf tag 7). Required for step counters to render properly.
- `Time.Hours` and `Time.Minutes`: Tens and Ones must use separate image index ranges. For example, assign Hours to images 1 through 10, and assign Minutes to images 11 through 20. Reusing the same image indices for both hours and minutes causes the display engine to misrender.

### 5. Preview image configuration

The watch face selection carousel on the band requires preview images to display a thumbnail:

```json
"Background": {
  "Image": { "X": 0, "Y": 0, "ImageIndex": 0 },
  "PreviewEN": { "X": 0, "Y": 0, "ImageIndex": 55 },
  "PreviewCN": { "X": 0, "Y": 0, "ImageIndex": 55 },
  "PreviewCN2": { "X": 0, "Y": 0, "ImageIndex": 55 }
}
```

The preview image must be 126x294 pixels in RGB format. Without `PreviewEN`, `PreviewCN`, and `PreviewCN2`, the band displays a blank box or a question mark in the on-device selection menu.

### 6. Static layout and widget placement

The band RTOS does not support conditional layout reflow. Coordinates in the binary are fixed.

If you design a low-battery indicator that stays hidden when battery is 20% or higher:
- Do not place the battery at the bottom of the screen (such as Y=258) while keeping steps in the middle (such as Y=216). When the battery is hidden, the bottom 50 pixels become empty space.
- Instead, anchor the step counter at the bottom curve of the capsule (Y=252 to 280), leaving a 14-pixel bottom margin.
- Place the low-battery warning badge in the gap between Minutes and Steps (Y=224). When the battery is healthy, the badge is transparent, leaving clean vertical separation. When the battery drops below 20%, the red or orange warning badge appears in the center slot.

## Recommended element coordinates

The following vertical ranges provide balanced spacing across the 294-pixel capsule:

| Element | Vertical range (Y) | Box size | Font size | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Weekday | 12 .. 32 | 44x20 px | 18 | Centered horizontally |
| Date | 36 .. 60 | 18x24 px | 22 | Formatted as MM/DD |
| Hours | 72 .. 137 | 44x65 px | 80 | Tens at X=17, Ones at X=65 |
| Minutes | 150 .. 215 | 44x65 px | 80 | Tens at X=17, Ones at X=65 |
| Battery | 224 .. 246 | 44x22 px | Badge | Hidden when >= 20% |
| Steps | 252 .. 280 | 22x28 px | 28 | Anchors bottom, 14px margin |

## Verification script

You can verify whether a packed `.bin` file satisfies these hardware rules using Node.js and `watchface-js`:

```javascript
const fs = require('fs');
const { getAvailableModels, parseWatchFaceBin } = require('watchface-js/dist/watchFaceBinTools/watchFaceBinParser.js');

const mb5 = getAvailableModels().find(m => m.id === 'miband5');
const buf = fs.readFileSync('bin/clean-night-10-blue.bin');
const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
const wf = parseWatchFaceBin(ab, mb5.fileType);

// Verify tags
if (wf.parameters.Time.DrawingOrder !== false) {
  throw new Error('Time.DrawingOrder must be false (Protobuf tag 11)');
}
if (wf.parameters.Activity.UnknownV7 !== 0) {
  throw new Error('Activity.UnknownV7 must be 0 (Protobuf tag 7)');
}

// Verify sprite buffer sizes
for (let i = 1; i < wf.images.length; i++) {
  const img = wf.images[i];
  if (img.pixelFormat === 0x64) {
    const bSize = 16 + 1024 + img.width * img.height;
    if (bSize > 4096) {
      throw new Error(`Image ${i} exceeds 4096 byte buffer: ${bSize} bytes`);
    }
  }
}
console.log('Binary verified hardware-safe');
```
