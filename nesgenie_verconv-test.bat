@echo off
cls

echo === Journey to Silius: US code XTUSKTAV to EUR (should find XTVSNTAV) ===
python nesgenie_verconv.py xtusktav test-in\journey.nes test-in\journey-e.nes
echo.

echo === Journey to Silius: US code TEXINTIA to EUR (should find TESSXTIA) ===
python nesgenie_verconv.py texintia test-in\journey.nes test-in\journey-e.nes
echo.

echo === Journey to Silius: US code TEXINTIA to US (should find TEXINTIA) ===
python nesgenie_verconv.py texintia test-in\journey.nes test-in\journey.nes
echo.

echo === Journey to Silius: EUR code TESSXTIA to US (should find TEXINTIA) ===
python nesgenie_verconv.py tessxtia test-in\journey-e.nes test-in\journey.nes
echo.

echo === Journey to Silius: EUR code TESSXTIA to US, slice len 17 (should find TEXINTIA) ===
python nesgenie_verconv.py --slice-length 17 tessxtia test-in\journey-e.nes test-in\journey.nes
echo.

echo === Journey to Silius: EUR code TESSXTIA to US, max diff 2 (should find TEXINTIA) ===
python nesgenie_verconv.py --max-different-bytes 2 tessxtia test-in\journey-e.nes test-in\journey.nes
echo.

echo === SMB 3: US code SLXPLOVS to JP (should find SLUPGOVS) ===
py nesgenie_verconv.py slxplovs test-in\smb3.nes test-in\smb3-j.nes
echo.

echo === Same but verbose (should find SLUPGOVS) ===
py nesgenie_verconv.py --verbose slxplovs test-in\smb3.nes test-in\smb3-j.nes
echo.

echo === Help text ===
python nesgenie_verconv.py --help
echo.

echo === These should cause errors ===
python nesgenie_verconv.py aaaaaaaa nonexistent1 nonexistent2