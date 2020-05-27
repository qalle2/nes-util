@echo off
rem WARNING: This batch file DELETES files. Run at your own risk.

if exist test-out\*.png del test-out\*.png
cls

echo === help ===
echo.
python nes_blaster_mapext.py --help
echo.

echo === default settings, US version ===
echo.
python nes_blaster_mapext.py test-in\blastermaster.nes test-out\default.png
echo.

echo === all maps, USB/SB/blocks output, US version ===
echo.
for /l %%i in (0,1,15) do python nes_blaster_mapext.py --map %%i --usb test-out\usb%%i.png --sb test-out\sb%%i.png --blocks test-out\blocks%%i.png test-in\blastermaster.nes test-out\world%%i.png & echo.

echo === all maps, USB/SB/blocks output, Japanese version ===
echo.
for /l %%i in (0,1,15) do python nes_blaster_mapext.py --japan --map %%i --usb test-out\usb%%ij.png --sb test-out\sb%%ij.png --blocks test-out\blocks%%ij.png test-in\blastermaster-j.nes test-out\world%%ij.png & echo.

echo === these should cause errors (incorrect game version) ===
echo.
python nes_blaster_mapext.py --map 9 test-in\blastermaster-j.nes test-out\error1.png
echo.
python nes_blaster_mapext.py --japan --map 9 test-in\blastermaster.nes test-out\error2.png
