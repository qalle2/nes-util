@echo off
cls

echo === Journey to Silius: US code XTUSKTAV to EUR (should find XTVSNTAV, but won't before partial matches are implemented) ===
python nesgenie_verconv.py xtusktav test-in\journey.nes test-in\journey-e.nes
echo.

echo === Journey to Silius: US code TEXINTIA to EUR (should find TESSXTIA) ===
python nesgenie_verconv.py texintia test-in\journey.nes test-in\journey-e.nes
echo.

echo === Journey to Silius: EUR code TESSXTIA to US (should find TEXINTIA) ===
python nesgenie_verconv.py tessxtia test-in\journey-e.nes test-in\journey.nes
echo.

echo === Help text ===
python nesgenie_verconv.py
echo.

echo === These should cause errors ===
python nesgenie_verconv.py aaaaaaaa nonexistent1 nonexistent2
