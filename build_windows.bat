@echo off
REM Build script for Windows

echo Building for Windows...

REM Clean previous builds
rmdir /s /q build dist 2>nul

REM Build the application
pyinstaller --name="MassEmailSender" ^
    --windowed ^
    --onefile ^
    --icon=app.ico ^
    --add-data ".;." ^
    --noconfirm ^
    main.py

echo Build complete! Application is in the 'dist' folder.
echo You can find: MassEmailSender.exe
pause
