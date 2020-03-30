@echo off
rem WARNING: this batch file DELETES some files. Run at your own risk.

cls
if exist test-out\*.png del test-out\*.png

echo === Decoding iNES ROM files ===
python nes_chr_decode.py test-in\smb1.nes test-out\smb1-chr1.png
python nes_chr_decode.py test-in\blastermaster.nes test-out\blastermaster-chr1.png
echo.

echo === Decoding raw CHR data files ===
python nes_chr_decode.py test-in\smb1.chr test-out\smb1-chr2.png
python nes_chr_decode.py --palette 0000ff ff0000 ff00ff 00ff00 test-in\smb1.chr test-out\smb1-chr3.png
python nes_chr_decode.py test-in\blastermaster.chr test-out\blastermaster-chr2.png
python nes_chr_decode.py test-in\chr-2color.chr test-out\chr-2color.png
echo.

echo === Verify the decoded files yourself ===
dir /b test-out\*.png
