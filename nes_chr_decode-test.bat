@echo off
rem WARNING: this batch file DELETES some files. Run at your own risk.

cls
if exist test-out\*.png del test-out\*.png

echo === Decoding ===
python nes_chr_decode.py test-in\smb1.chr test-out\smb1-chr.png
python nes_chr_decode.py --palette 0000ff ff0000 ff00ff 00ff00 test-in\smb1.chr test-out\smb1-chr-altcolor.png
python nes_chr_decode.py test-in\blastermaster.chr test-out\blastermaster-chr.png
echo.

echo === Verify the decoded files yourself ===
dir /b test-out\*.png
