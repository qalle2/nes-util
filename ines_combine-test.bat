@echo off
rem WARNING: This batch file DELETES files. Run at your own risk.

cls
if exist test-out\*.nes del test-out\*.nes

echo === Help ===
python ines_combine.py --help
echo.

echo === Creating iNES files ===
python ines_combine.py --prg-rom test-in\blastermaster.prg --chr-rom test-in\blastermaster.chr --mapper 1 --mirroring h test-out\blastermaster.nes
python ines_combine.py --prg-rom test-in\smb1.prg --chr-rom test-in\smb1.chr --mapper 0 --mirroring v test-out\smb1.nes
python ines_combine.py --prg-rom test-in\videomation.prg --mapper 13 --mirroring v test-out\videomation.nes
python ines_combine.py --prg-rom test-in\zelda1.prg --chr-rom test-in\empty.chr --mapper 1 --mirroring h --save-ram test-out\zelda1.nes
echo.

echo === Validating iNES files ===
fc /b test-in\blastermaster.nes test-out\blastermaster.nes
fc /b test-in\smb1.nes test-out\smb1.nes
fc /b test-in\videomation.nes test-out\videomation.nes
fc /b test-in\zelda1.nes test-out\zelda1.nes

if exist test-out\*.nes del test-out\*.nes
