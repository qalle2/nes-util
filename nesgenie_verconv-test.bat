@echo off
cls

echo === Excitebike: US code SXZTYU to 15-in-1 multicart (should find SXXTYUVV) ===
echo.
python nesgenie_verconv.py sxztyu test-in\excitebike.nes test-in\15in1.nes
echo.

echo === Excitebike: 15-in-1 multicart code SXXTYUVV to US (should find SXZTYU) ===
echo.
python nesgenie_verconv.py sxxtyuvv test-in\15in1.nes test-in\excitebike.nes
echo.

echo === Journey to Silius: US code XTUSKTAV to EUR (should find XTVSNTAV) ===
echo.
python nesgenie_verconv.py xtusktav test-in\journey.nes test-in\journey-e.nes
echo.

echo === Journey to Silius: US code XTUSKTAV to EUR, slice length=1/1 (should find XTVSNTAV) ===
echo.
python nesgenie_verconv.py xtusktav --slice-length-before 1 --slice-length-after 1 test-in\journey.nes test-in\journey-e.nes
echo.

echo === Journey to Silius: US code XTUSKTAV to EUR, max different bytes=6 (should find XTVSNTAV) ===
echo.
python nesgenie_verconv.py xtusktav --max-different-bytes 6 test-in\journey.nes test-in\journey-e.nes
echo.

echo === Journey to Silius: US code TEXINTIA to EUR (should find TESSXTIA) ===
echo.
python nesgenie_verconv.py texintia test-in\journey.nes test-in\journey-e.nes
echo.

echo === Journey to Silius: EUR code TESSXTIA to US (should find TEXINTIA) ===
echo.
python nesgenie_verconv.py tessxtia test-in\journey-e.nes test-in\journey.nes
echo.

echo === SMB: US code SXIOPO to same version (should find SXIOPO) ===
echo.
python nesgenie_verconv.py sxiopo test-in\smb1.nes test-in\smb1.nes
echo.

echo === SMB: US code NYAAAE (8000:ff) to same version (should find NYAAAE) ===
echo.
python nesgenie_verconv.py nyaaae test-in\smb1.nes test-in\smb1.nes
echo.

echo === SMB: US code AEYNNY (ffff:00) to same version (should find AEYNNY) ===
echo.
python nesgenie_verconv.py aeynny test-in\smb1.nes test-in\smb1.nes
echo.

echo === SMB 3: US code SLXPLOVS to JP (should find SLUPGOVS) ===
echo.
python nesgenie_verconv.py slxplovs test-in\smb3.nes test-in\smb3-j.nes
echo.

echo === SMB 3: US code SLZPLO to JP (should refuse the code) ===
echo.
python nesgenie_verconv.py slzplo test-in\smb3.nes test-in\smb3-j.nes
echo.

echo === User's code should do nothing with file1 ===
echo.
python nesgenie_verconv.py eaeaeaea test-in\smb3.nes test-in\smb1.nes
echo.

echo === file2 shouldn't be compatible with what the code does ===
echo.
python nesgenie_verconv.py yeuzugaa test-in\smb3.nes test-in\smb1.nes
echo.

echo === These should cause errors ===
echo.
python nesgenie_verconv.py dapapa test-in\smb1.nes test-in\smb1.nes
python nesgenie_verconv.py aaaaaaaa nonexistent1 nonexistent2
python nesgenie_verconv.py aaaaaa test-in\invalid-id.nes test-in\smb1.nes
echo.

echo === Help text ===
echo.
python nesgenie_verconv.py --help
