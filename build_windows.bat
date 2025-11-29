@echo off
REM Build script for Windows

echo Building for Windows...

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build the application
pyinstaller --name="MassEmailSender" ^
    --windowed ^
    --onefile ^
    --icon=assets/app.ico ^
    --add-data ".;." ^
    --noconfirm ^
    main.py

echo Build complete! Application is in the 'dist' folder.
echo You can find: MassEmailSender.exe
pause
