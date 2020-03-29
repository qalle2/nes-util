@echo off
cls

echo === Help ===
python ines_info.py
echo.

echo === Printing info ===
for %%f in (test-in\*.nes) do python ines_info.py "%%f" & echo.

echo === This should cause an error ===
python ines_info.py nonexistent
