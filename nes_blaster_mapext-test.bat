@echo off
rem WARNING: This batch file DELETES files. Run at your own risk.

if exist test-out\*.png del test-out\*.png
cls

echo === test.bat: help ===
echo.
python nes_blaster_mapext.py --help
echo.

echo === test.bat: default settings ===
echo.
python nes_blaster_mapext.py test-in\blastermaster.nes test-out\default.png
echo.

echo === test.bat: all maps, USB/SB/blocks output ===
echo.
for /l %%i in (0,1,15) do python nes_blaster_mapext.py --map %%i --usb test-out\usb%%i.png --sb test-out\sb%%i.png --blocks test-out\blocks%%i.png test-in\blastermaster.nes test-out\world%%i.png & echo.
