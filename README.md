# Key Lock Notifier

![Key Lock Notifier Logo](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgWV1bFi6RmdiTiYuIjQjiCa1bMVIWjDm3rzGr6ULzXnx3v8ZyRyVrznK2lEThfGhNGJmzGoIQ6hyphenhyphenkc0zxRxmYkMQaukx76HAaWT6Z9ZsF6pukl_XIP8BYF3DNxkfkSqnAKkr8-xu36Y2LJtcwv3hRCGQd3TwT5FGh5AiEl-NEDrnid2I11OHvTTX47b6U/s16000/app_logo.png)


## Overview

Key Lock Notifier is a Windows application that displays elegant on-screen notifications whenever you toggle Caps Lock, Num Lock, or Scroll Lock keys. It provides visual feedback with customizable settings to enhance your typing experience.

## Features

- 💬 **Real-time notifications** for Caps Lock, Num Lock, and Scroll Lock state changes
- 🎨 **Modern dark theme interface** with blue accent colors
- ⚙️ **Customizable settings** to show/hide specific key notifications
- 🚀 **System tray integration** for easy access to settings and controls
- 🖥️ **Windows startup option** to run automatically when your computer starts
- 💤 **Low resource usage** runs silently in the background

## Screenshots

| Caps Lock On | Num Lock Off | Settings Window |
|:------------:|:------------:|:---------------:|
| ![Caps Lock On](images/caps_on.png) | ![Num Lock Off](images/num_off.png) | ![Settings](images/settings_screenshot.png) |

## Installation

### Prerequisites
- Windows operating system
- Python 3.6 or higher
- Required libraries: tkinter, PIL (Pillow), keyboard, ctypes

### Method 1: Using the Executable (Recommended)
1. Download the latest release from the [Releases page](https://github.com/captainmgc/key-lock-notifier/releases)
2. Extract the ZIP file to a location of your choice
3. Run `KeyLockNotifier.exe` to start the application

### Method 2: From Source
1. Clone the repository
   ```
   git clone https://github.com/captainmgc/key-lock-notifier.git
   ```
2. Install the required dependencies
   ```
   pip install -r requirements.txt
   ```
3. Run the application
   ```
   python key-lock-notifier.py
   ```

## Usage

1. **System Tray Icon**: Once launched, the application runs in the system tray. Right-click on the icon to access the settings or exit the application.
2. **Settings**: Configure which lock keys should trigger notifications and whether the application should start with Windows.
3. **Notifications**: When you press Caps Lock, Num Lock, or Scroll Lock, a notification will appear on your screen showing the current state (ON/OFF).

## Customization

The application stores its configuration in a JSON file located at `%USERPROFILE%\key_lock_notifier_config.json`. You can manually edit this file if needed, but it's recommended to use the settings interface.

### Default Configuration

```json
{
    "show_caps_lock": true,
    "show_num_lock": true,
    "show_scroll_lock": true,
    "start_with_windows": false,
    "theme": "blue_dark"
}
```

## Building from Source

To build the executable:

1. Install PyInstaller
   ```
   pip install pyinstaller
   ```

2. Build the executable
   ```
   pyinstaller --onefile --windowed --icon=images/app_icon.ico --add-data "images;images" key-lock-notifier.py
   ```

## Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests for any improvements or bug fixes.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Created by [captainmgc](https://github.com/captainmgc)
- Special thanks to all contributors and testers

## Contact

If you have any questions or suggestions, feel free to open an issue on GitHub or contact me directly through my GitHub profile.

---

Made with ❤️ by captainmgc
