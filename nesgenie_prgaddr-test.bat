@echo off
cls

echo === Excitebike, AAAAAA ===
python nesgenie_prgaddr.py test-in\excitebike.nes aaaaaa
echo.

echo === SMB, SXIOPO ===
python nesgenie_prgaddr.py test-in\smb1.nes sxiopo
echo.

echo === Blaster Master (US), XTVYGGAV ===
python nesgenie_prgaddr.py test-in\blastermaster.nes xtvyggav
echo.

echo === Blaster Master (EUR), AASTKETG ===
python nesgenie_prgaddr.py test-in\blastermaster-e.nes aastketg
echo.

echo === SMB3, YEUZUGAA ===
python nesgenie_prgaddr.py test-in\smb3.nes yeuzugaa
echo.

echo === SMB3, YEUZUGPA (shouldn't find any) ===
python nesgenie_prgaddr.py test-in\smb3.nes yeuzugpa

echo === Nonexistent file ===
python nesgenie_prgaddr.py nonexistent aaaaaa
echo.

echo === Invalid code ===
python nesgenie_prgaddr.py test-in\smb1.nes dapapa
echo.

echo === Help ===
python nesgenie_prgaddr.py
