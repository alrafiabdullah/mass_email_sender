#!/bin/bash
# Build script for macOS

echo "Building for macOS..."

# Clean previous builds
rm -r build dist

# Build the application
pyinstaller --name="MassEmailSender" \
    --windowed \
    --onefile \
    --icon=app.icns \
    --add-data ".:." \
    --noconfirm \
    main.py

echo "Build complete! Application is in the 'dist' folder."
echo "You can find: MassEmailSender.app"
