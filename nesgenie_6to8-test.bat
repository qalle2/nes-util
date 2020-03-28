@echo off
cls

echo === test.bat: Super Mario Bros. ===
python nesgenie_6to8.py nesgenie_6to8-test\smb1.nes sxiopo
echo.

echo === test.bat: R.C. Pro-Am (shouldn't find any codes) ===
python nesgenie_6to8.py nesgenie_6to8-test\rc-pro-am.nes nnynnn
echo.

echo === test.bat: Blaster Master - EAGPOA (correct result only) ===
python nesgenie_6to8.py nesgenie_6to8-test\blaster.nes eagpoa | find "EAKPOATA"
echo.

echo === test.bat: Blaster Master - EAGPOA ===
python nesgenie_6to8.py nesgenie_6to8-test\blaster.nes eagpoa
echo.

echo === test.bat: Blaster Master - SZLGYI (correct result only) ===
python nesgenie_6to8.py nesgenie_6to8-test\blaster.nes szlgyi | find "SZUGYIVG"
echo.

echo === test.bat: Blaster Master - SZLGYI ===
python nesgenie_6to8.py nesgenie_6to8-test\blaster.nes szlgyi
echo.

echo === test.bat: Mega Man (correct result only) ===
python nesgenie_6to8.py nesgenie_6to8-test\megaman1.nes ozikpx | find "OZSKPZVK"
echo.

echo === test.bat: Mega Man ===
python nesgenie_6to8.py nesgenie_6to8-test\megaman1.nes ozikpx
echo.

echo === test.bat: Batman - Return of the Joker (correct result only) ===
python nesgenie_6to8.py nesgenie_6to8-test\batmanjoker.nes szzzon | find "SZXZONSE"
echo.

echo === test.bat: Batman - Return of the Joker ===
python nesgenie_6to8.py nesgenie_6to8-test\batmanjoker.nes szzzon
echo.

echo === test.bat: Super Mario Bros. 3 (correct result only) ===
python nesgenie_6to8.py nesgenie_6to8-test\smb3.nes yelzug | find "YEUZUGAA"
echo.

echo === test.bat: Super Mario Bros. 3 ===
python nesgenie_6to8.py nesgenie_6to8-test\smb3.nes yelzug
echo.

echo === test.bat: Action 52 (unsupported mapper; omitting codes from output) ===
python nesgenie_6to8.py nesgenie_6to8-test\action52.nes aaaaaa | find /v "AAEAA"
echo.

echo === test.bat: these should cause errors ===
python nesgenie_6to8.py
python nesgenie_6to8.py nonexistent aaaaaa
python nesgenie_6to8.py nesgenie_6to8-test\smb1.nes dddddd
