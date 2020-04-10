@echo off
rem WARNING: This batch file will DELETE some files. Run at your own risk.

cls
if exist test-out\*.prg del test-out\*.prg
if exist test-out\*.chr del test-out\*.chr

echo === Help ===
python ines_split.py --help
echo.

echo === Splitting ===
python ines_split.py --prg test-out\smb1.prg --chr test-out\smb1.chr test-in\smb1.nes
python ines_split.py --prg test-out\blastermaster.prg test-in\blastermaster.nes
python ines_split.py --chr test-out\blastermaster.chr test-in\blastermaster.nes
echo.

echo === Validating output files ===
fc /b test-in\smb1.prg test-out\smb1.prg
fc /b test-in\smb1.chr test-out\smb1.chr
fc /b test-in\blastermaster.prg test-out\blastermaster.prg
fc /b test-in\blastermaster.chr test-out\blastermaster.chr

if exist test-out\*.prg del test-out\*.prg
if exist test-out\*.chr del test-out\*.chr

echo === All of these should cause an error ===
python ines_split.py
python ines_split.py --nonexistent test-in\smb1.nes
python ines_split.py test-in\smb1.nes
python ines_split.py --prg test-in\smb1.nes test-in\smb1.nes
python ines_split.py --chr test-in\smb1.nes test-in\smb1.nes
python ines_split.py --prg test-out\out.prg test-in\too-small.nes
