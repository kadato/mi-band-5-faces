# Install a custom face on Mi Band 5

To install a face on your band, transfer the compiled `.bin` file, such as `bin/clean-night-18-custom.bin`, to your phone.
You can move the file using USB, local network sharing, or email.

## Install with Notify for Mi Band on Android

This method keeps your pairing with Mi Fit or Zepp Life intact.

1. Ensure your band is charged, Bluetooth is active, and the band is paired in Mi Fit or Zepp Life.
2. Install Notify for Mi Band from Google Play and open the app. The free version includes the watch face installer.
3. Open the watch face section under Tools, then tap the custom watch face option.
4. Select `bin/clean-night-18-custom.bin` and start the transfer.
5. Keep your phone near the band until the transfer finishes, which takes one to two minutes. The band displays an update progress screen during the process. Do not interact with the band while the transfer is active.

## Install with Gadgetbridge on Android

Gadgetbridge is an open source manager that operates without a Xiaomi account.

1. Unpair the band from Mi Fit or Zepp Life. A band connects to only one companion app at a time.
2. Install Gadgetbridge, then pair your band inside the app.
3. Open `bin/clean-night-18-custom.bin` using any Android file manager, tap Share, and select Gadgetbridge. You can also use the firmware installation action within Gadgetbridge.
4. Keep the phone near the band until installation completes.

## Install on iOS

iOS cannot sideload `.bin` watch face files directly over Bluetooth. To install on an iPhone setup, borrow an Android device for two minutes. Pair the band with the Android phone, install the `.bin` file using Notify for Mi Band or Gadgetbridge, and re-pair the band with your iPhone. The installed watch face remains active on the band.

## Switch faces on the band

- Long press the band home screen or go to More, then Band display to switch between saved faces.
- The battery icon stays hidden when the battery charge is 20% or higher.
- The icon appears in orange between 10% and 19% charge, and turns red below 10% charge.
- If a transfer fails, keep the band charged, keep the phone within one meter, and retry the transfer without interacting with the band display.

## Custom layout details

The `bin/clean-night-18-custom.bin` build places the weekday and date at the top, followed by large stacked hour and minute digits. Steps anchor the bottom curve of the capsule, and the low-battery warning badge appears in the slot between minutes and steps when battery drops below 20%.

### Screen limits and adjustments

1. Time digits use 44x65 pixel boxes (Font 80). The Mi Band 5 display is 126x294 pixels, and the display blitter limits sprite areas to 3056 pixels (4096-byte line buffer limit).
2. The hour digits start at Y=72 and minutes start at Y=150. This leaves room for the weekday and date above the time block, and steps at Y=252.
