@echo off
cls

echo === Super Mario Bros. ===
python nesgenie_6to8.py test-in\smb1.nes sxiopo
echo.

echo === R.C. Pro-Am (shouldn't find any codes) ===
python nesgenie_6to8.py test-in\rcproam1.nes nnynnn
echo.

echo === Blaster Master - EAGPOA (correct result only) ===
python nesgenie_6to8.py test-in\blastermaster.nes eagpoa | find "EAKPOATA"
echo.

echo === Blaster Master - EAGPOA ===
python nesgenie_6to8.py test-in\blastermaster.nes eagpoa
echo.

echo === Blaster Master - SZLGYI (correct result only) ===
python nesgenie_6to8.py test-in\blastermaster.nes szlgyi | find "SZUGYIVG"
echo.

echo === Blaster Master - SZLGYI ===
python nesgenie_6to8.py test-in\blastermaster.nes szlgyi
echo.

echo === Mega Man (correct result only) ===
python nesgenie_6to8.py test-in\megaman1.nes ozikpx | find "OZSKPZVK"
echo.

echo === Mega Man ===
python nesgenie_6to8.py test-in\megaman1.nes ozikpx
echo.

echo === Batman - Return of the Joker (correct result only) ===
python nesgenie_6to8.py test-in\batmanjoker.nes szzzon | find "SZXZONSE"
echo.

echo === Batman - Return of the Joker ===
python nesgenie_6to8.py test-in\batmanjoker.nes szzzon
echo.

echo === Super Mario Bros. 3 (correct result only) ===
python nesgenie_6to8.py test-in\smb3.nes yelzug | find "YEUZUGAA"
echo.

echo === Super Mario Bros. 3 ===
python nesgenie_6to8.py test-in\smb3.nes yelzug
echo.

echo === Action 52 (unknown mapper; omitting codes from output) ===
python nesgenie_6to8.py test-in\action52.nes aaaaaa | find /v "AAEAA"
echo.

echo === These should cause errors ===
python nesgenie_6to8.py
python nesgenie_6to8.py nonexistent aaaaaa
python nesgenie_6to8.py test-in\smb1.nes dddddd
python nesgenie_6to8.py test-in\invalid-id.nes aaaaaa
