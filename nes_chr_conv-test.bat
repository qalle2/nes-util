@echo off
rem WARNING: this batch file DELETES some files. Run at your own risk.

cls
if exist test-out\*.chr del test-out\*.chr
if exist test-out\*.png del test-out\*.png

echo === Decoding ===
python nes_chr_conv.py d test-in\smb1.chr test-out\smb1-chr.png
python nes_chr_conv.py --palette 0000ff ff0000 ff00ff 00ff00 d test-in\smb1.chr test-out\smb1-chr-altcolor.png
python nes_chr_conv.py d test-in\blastermaster.chr test-out\blastermaster-chr.png
echo.

echo === Verify the decoded files yourself ===
dir /b test-out\*.png
echo.

echo === Encoding ===
python nes_chr_conv.py e test-in\smb1-chr.png test-out\smb1a.chr
python nes_chr_conv.py --palette 0000ff ff0000 ff00ff 00ff00 e test-in\smb1-chr-altcolor.png test-out\smb1b.chr
python nes_chr_conv.py e test-in\blastermaster-chr.png test-out\blastermaster.chr
echo.

echo === Verifying encoded files ===
fc /b test-in\smb1.chr test-out\smb1a.chr
fc /b test-in\smb1.chr test-out\smb1b.chr
fc /b test-in\blastermaster.chr test-out\blastermaster.chr
if exist test-out\*.chr del test-out\*.chr
