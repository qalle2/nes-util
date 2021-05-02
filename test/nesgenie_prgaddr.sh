clear

echo "=== Excitebike, AAAAAA ==="
python3 ../nesgenie_prgaddr.py ../test-in/excitebike.nes aaaaaa
echo

echo "=== SMB, SXIOPO ==="
python3 ../nesgenie_prgaddr.py ../test-in/smb1.nes sxiopo
echo

echo "=== Blaster Master (US), XTVYGGAV ==="
python3 ../nesgenie_prgaddr.py ../test-in/blastermaster.nes xtvyggav
echo

echo "=== Blaster Master (EUR), AASTKETG ==="
python3 ../nesgenie_prgaddr.py ../test-in/blastermaster-e.nes aastketg
echo

echo "=== SMB3, YEUZUGAA ==="
python3 ../nesgenie_prgaddr.py ../test-in/smb3.nes yeuzugaa
echo

echo "=== SMB3, YELZUG (should find all of the above and more) ==="
python3 ../nesgenie_prgaddr.py ../test-in/smb3.nes yelzug
echo

echo "=== SMB3, YEUZUGPA (shouldn't find any) ==="
python3 ../nesgenie_prgaddr.py ../test-in/smb3.nes yeuzugpa

echo "=== Videomation, AAAAAA (should print a warning) ==="
python3 ../nesgenie_prgaddr.py ../test-in/videomation.nes aaaaaa
echo

echo "=== These should cause two errors ==="
python3 ../nesgenie_prgaddr.py ../test-in/smb1.nes dapapa
python3 ../nesgenie_prgaddr.py ../test-in/invalid-id.nes sxiopo
echo
