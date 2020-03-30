@echo off
rem WARNING: this batch file DELETES some files. Run at your own risk.

cls
if exist test-out\*.chr del test-out\*.chr

echo === Encoding ===
python nes_chr_encode.py test-in\smb1-chr.png test-out\smb1a.chr
python nes_chr_encode.py test-in\smb1-chr-grayscale.png test-out\smb1b.chr
python nes_chr_encode.py test-in\smb1-chr-rgb.png test-out\smb1c.chr
python nes_chr_encode.py --palette 0000ff ff0000 ff00ff 00ff00 test-in\smb1-chr-altcolor.png test-out\smb1d.chr
python nes_chr_encode.py test-in\smb1-chr.gif test-out\smb1e.chr
python nes_chr_encode.py test-in\blastermaster-chr.png test-out\blastermaster.chr
python nes_chr_encode.py test-in\chr-2color.png test-out\chr-2color.chr
echo.

echo === Verifying encoded files ===
fc /b test-in\smb1.chr test-out\smb1a.chr
fc /b test-in\smb1.chr test-out\smb1b.chr
fc /b test-in\smb1.chr test-out\smb1c.chr
fc /b test-in\smb1.chr test-out\smb1d.chr
fc /b test-in\smb1.chr test-out\smb1e.chr
fc /b test-in\blastermaster.chr test-out\blastermaster.chr
fc /b test-in\chr-2color.chr test-out\chr-2color.chr

if exist test-out\*.chr del test-out\*.chr
