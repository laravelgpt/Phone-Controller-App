# Phone Controller App

A Windows application to control your Android phone from your PC using [scrcpy](https://github.com/Genymobile/scrcpy) and ADB.

## Features

- **Mirror Android Screen**: View your Android device's screen in real-time on your PC.
- **Full Device Control**: Interact with your phone using mouse and keyboard (tap, swipe, type, etc.).
- **No Root Required**: Works with most Android devices without root access.
- **High Performance**: Low latency and high frame rate screen mirroring.
- **File Transfer**: Drag and drop files between your PC and Android device.
- **Multi-Device Support**: Connect and control multiple devices simultaneously.
- **Customizable Resolution & Bitrate**: Adjust video quality and performance to your needs.
- **Clipboard Synchronization**: Copy and paste text between your PC and Android device.
- **Audio Forwarding**: (If supported) Forward device audio to your PC.
- **Portable**: No installation required; just run the executable.
- **Easy Setup**: Includes all necessary binaries (scrcpy, adb) for quick start.

## Getting Started

1. **Connect your Android device** via USB and enable USB debugging.
2. **Run the application** (e.g., `main.py` or use the provided scripts in the `scrcpy` folder).
3. **Control your device** from the PC window that appears.

## Requirements

- Windows 10 or later
- Python 3.x (if running `main.py`)
- Android device with USB debugging enabled

## Included Tools

- [scrcpy](https://github.com/Genymobile/scrcpy)
- [ADB (Android Debug Bridge)](https://developer.android.com/studio/command-line/adb)

## Configuration

Edit `config.json` to customize settings such as default resolution, bitrate, or device selection.

## License

This project is licensed under the MIT License. See [LICENSE.md](LICENSE.md) for details.

---

For more information, visit the [GitHub repository](https://github.com/laravelgpt/Phone-Controller-App).
