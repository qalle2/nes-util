@echo off
cls

echo === Batman - Return of the Joker - SZZZON (should find SZXZONSE) ===
python nesgenie_6to8.py test-in\batmanjoker.nes szzzon
echo.

echo === Blaster Master - EAGPOA (should find EAKPOATA) ===
python nesgenie_6to8.py test-in\blastermaster.nes eagpoa
echo.

echo === Blaster Master - SZLGYI (should find SZUGYIVG) ===
python nesgenie_6to8.py test-in\blastermaster.nes szlgyi
echo.

echo === Mega Man - OZIKPX (should find OZSKPZVK) ===
python nesgenie_6to8.py test-in\megaman1.nes ozikpx
echo.

echo === R.C. Pro-Am (shouldn't find any codes) ===
python nesgenie_6to8.py test-in\rcproam1.nes nnynnn

echo === Super Mario Bros. ===
python nesgenie_6to8.py test-in\smb1.nes sxiopo
echo.

echo === Super Mario Bros. 3 - YELZUG (should find YEUZUGAA) ===
python nesgenie_6to8.py test-in\smb3.nes yelzug
echo.

echo === These should cause errors ===
python nesgenie_6to8.py
python nesgenie_6to8.py nonexistent aaaaaa
python nesgenie_6to8.py test-in\smb1.nes dddddd
python nesgenie_6to8.py test-in\invalid-id.nes aaaaaa
