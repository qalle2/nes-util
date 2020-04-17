@echo off
cls

echo === Excitebike: US code SXZTYU to 15-in-1 multicart (should find SXXTYUVV) ===
python nesgenie_verconv.py sxztyu test-in\excitebike.nes test-in\15in1.nes
echo.

echo === Excitebike: 15-in-1 multicart code SXXTYUVV to US (should find SXZTYU) ===
python nesgenie_verconv.py sxxtyuvv test-in\15in1.nes test-in\excitebike.nes
echo.

echo === Journey to Silius: US code XTUSKTAV to EUR (should find XTVSNTAV) ===
python nesgenie_verconv.py xtusktav test-in\journey.nes test-in\journey-e.nes
echo.

echo === Journey to Silius: US code TEXINTIA to EUR (should find TESSXTIA) ===
python nesgenie_verconv.py texintia test-in\journey.nes test-in\journey-e.nes
echo.

echo === Journey to Silius: EUR code TESSXTIA to US, slice len 5 (should find TEXINTIA) ===
python nesgenie_verconv.py --slice-length 7 tessxtia test-in\journey-e.nes test-in\journey.nes
echo.

echo === Journey to Silius: EUR code TESSXTIA to US, max diff 2 (should find TEXINTIA) ===
python nesgenie_verconv.py --max-different-bytes 2 tessxtia test-in\journey-e.nes test-in\journey.nes
echo.

echo === SMB: US code SXIOPO to same version (should find SXIOPO) ===
python nesgenie_verconv.py --verbose sxiopo test-in\smb1.nes test-in\smb1.nes
echo.

echo === SMB 3: US code SLXPLOVS to JP (should find SLUPGOVS) ===
python nesgenie_verconv.py --verbose slxplovs test-in\smb3.nes test-in\smb3-j.nes
echo.

echo === Help text ===
python nesgenie_verconv.py --help
echo.

echo === These should cause errors ===
python nesgenie_verconv.py aaaaaaaa nonexistent1 nonexistent2
