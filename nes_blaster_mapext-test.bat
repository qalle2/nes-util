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

echo === test.bat: all maps, USB output ===
echo.
python nes_blaster_mapext.py --map 0 --usb test-out\usb00.png test-in\blastermaster.nes test-out\00.png
echo.
python nes_blaster_mapext.py --map 1 --usb test-out\usb01.png test-in\blastermaster.nes test-out\01.png
echo.
python nes_blaster_mapext.py --map 2 --usb test-out\usb02.png test-in\blastermaster.nes test-out\02.png
echo.
python nes_blaster_mapext.py --map 3 --usb test-out\usb03.png test-in\blastermaster.nes test-out\03.png
echo.
python nes_blaster_mapext.py --map 4 --usb test-out\usb04.png test-in\blastermaster.nes test-out\04.png
echo.
python nes_blaster_mapext.py --map 5 --usb test-out\usb05.png test-in\blastermaster.nes test-out\05.png
echo.
python nes_blaster_mapext.py --map 6 --usb test-out\usb06.png test-in\blastermaster.nes test-out\06.png
echo.
python nes_blaster_mapext.py --map 7 --usb test-out\usb07.png test-in\blastermaster.nes test-out\07.png
echo.
python nes_blaster_mapext.py --map 8 --usb test-out\usb08.png test-in\blastermaster.nes test-out\08.png
echo.
python nes_blaster_mapext.py --map 9 --usb test-out\usb09.png test-in\blastermaster.nes test-out\09.png
echo.
python nes_blaster_mapext.py --map 10 --usb test-out\usb10.png test-in\blastermaster.nes test-out\10.png
echo.
python nes_blaster_mapext.py --map 11 --usb test-out\usb11.png test-in\blastermaster.nes test-out\11.png
echo.
python nes_blaster_mapext.py --map 12 --usb test-out\usb12.png test-in\blastermaster.nes test-out\12.png
echo.
python nes_blaster_mapext.py --map 13 --usb test-out\usb13.png test-in\blastermaster.nes test-out\13.png
echo.
python nes_blaster_mapext.py --map 14 --usb test-out\usb14.png test-in\blastermaster.nes test-out\14.png
echo.
python nes_blaster_mapext.py --map 15 --usb test-out\usb15.png test-in\blastermaster.nes test-out\15.png
