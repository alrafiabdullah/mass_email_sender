# Building Mass Email Sender

This document explains how to build standalone executables for macOS and Windows.

## Prerequisites

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Make sure all dependencies are installed:
   ```bash
   pip install PyQt6 polars boto3
   ```

**Note**: `boto3` is required for AWS SES support. If you don't need SES, you can omit it.

## Building for macOS

On macOS, run:
```bash
chmod +x build_mac.sh
./build_mac.sh
```

This will create:
- `dist/MassEmailSender.app` - A macOS application bundle

### Optional: Add an Icon (macOS)
1. Create or download an `.icns` file
2. Save it as `app.icns` in the project directory
3. Run the build script again

## Building for Windows

On Windows, run:
```cmd
build_windows.bat
```

This will create:
- `dist/MassEmailSender.exe` - A Windows executable

### Optional: Add an Icon (Windows)
1. Create or download an `.ico` file
2. Save it as `app.ico` in the project directory
3. Run the build script again

## Advanced: Using the Spec File

For more control over the build process:

```bash
pyinstaller build_spec.py
```

## Cross-Platform Notes

- **Building for Windows on macOS (or vice versa)**: PyInstaller does not support cross-compilation. You must build on the target platform.
- To build for Windows, you need to run the build script on a Windows machine.
- To build for macOS, you need to run the build script on a macOS machine.

## Build Options Explained

- `--windowed` / `--noconsole`: Don't show a console window (GUI only)
- `--onefile`: Package everything into a single executable
- `--icon`: Add a custom application icon
- `--name`: Set the application name
- `--add-data`: Include additional files in the bundle

## Distribution

### macOS
- Distribute the entire `.app` bundle
- Users can drag it to their Applications folder
- Consider code signing for better compatibility (requires Apple Developer account)

### Windows
- Distribute the `.exe` file
- Consider creating an installer using tools like Inno Setup or NSIS
- Consider code signing to avoid Windows SmartScreen warnings

## Troubleshooting

### Large File Size
The executable may be large. To reduce size:
- Use `--onedir` instead of `--onefile` (creates a folder with dependencies)
- Exclude unnecessary packages
- Use UPX compression (already enabled in scripts)

### Antivirus False Positives
Some antivirus software may flag PyInstaller executables. This is common and usually a false positive.
