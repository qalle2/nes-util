@echo off
cls

echo === test.bat: help ===
python ines_info.py
echo.

echo === test.bat: normal output ===
for %%f in (ines_info-test\*.nes) do python ines_info.py "%%f" & echo.

echo === test.bat: these should cause errors ===
python ines_info.py nonexistent
python ines_info.py file1 file2
