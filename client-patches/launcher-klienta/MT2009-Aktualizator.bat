@echo off
rem MT2009 PLUS - aktualizator klienta. Lezy w folderze klienta, obok metin2client.exe.
rem "start" konczy ten plik od razu: aktualizacja moze go bezpiecznie podmienic,
rem bo cmd.exe nie czyta go juz dalej. Bledy pokazuje samo okno aktualizatora.
rem Gdy okno sie nie pokazuje: MT2009-Aktualizator.bat konsola (widoczna konsola z bledem).
if /i "%~1"=="konsola" (
  powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -NoExit -File "%~dp0MT2009-Aktualizator.ps1"
  exit /b
)
start "MT2009 PLUS" /min powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0MT2009-Aktualizator.ps1"
exit /b 0
