@echo off
rem WARNING: This batch file will DELETE some files. Run at your own risk.

if not exist ines_split-test\*.* goto error

cls
if exist ines_split-test\*.prg del ines_split-test\*.prg
if exist ines_split-test\*.chr del ines_split-test\*.chr

echo === test.bat: splitting ===
python ines_split.py --prg ines_split-test\genie.prg --chr ines_split-test\genie.chr ines_split-test\genie.nes
python ines_split.py --prg ines_split-test\smb.prg --chr ines_split-test\smb.chr ines_split-test\smb.nes
python ines_split.py --prg ines_split-test\blaster.prg ines_split-test\blaster.nes
python ines_split.py --chr ines_split-test\blaster.chr ines_split-test\blaster.nes
echo.

echo === test.bat: validating output files ===
fc /b ines_split-test\genie.correct-prg ines_split-test\genie.prg
fc /b ines_split-test\genie.correct-chr ines_split-test\genie.chr
fc /b ines_split-test\smb.correct-prg ines_split-test\smb.prg
fc /b ines_split-test\smb.correct-chr ines_split-test\smb.chr
fc /b ines_split-test\blaster.correct-prg ines_split-test\blaster.prg
fc /b ines_split-test\blaster.correct-chr ines_split-test\blaster.chr

echo === test.bat: all of these should cause an error ===
python ines_split.py
python ines_split.py --nonexistent ines_split-test\smb.nes
python ines_split.py ines_split-test\smb.nes
python ines_split.py --prg ines_split-test\smb.nes ines_split-test\smb.nes
python ines_split.py --chr ines_split-test\smb.nes ines_split-test\smb.nes
