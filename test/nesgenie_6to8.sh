clear

echo "=== Batman - Return of the Joker - SZZZON (should find SZXZONSE) ==="
python3 ../nesgenie_6to8.py ../test-in/batmanjoker.nes szzzon
echo

echo "=== Blaster Master - EAGPOA (should find EAKPOATA) ==="
python3 ../nesgenie_6to8.py ../test-in/blastermaster.nes eagpoa
echo

echo "=== Blaster Master - SZLGYI (should find SZUGYIVG) ==="
python3 ../nesgenie_6to8.py ../test-in/blastermaster.nes szlgyi
echo

echo "=== Mega Man - OZIKPX (should find OZSKPZVK) ==="
python3 ../nesgenie_6to8.py ../test-in/megaman1.nes ozikpx
echo

echo "=== R.C. Pro-Am (shouldn't find any codes) ==="
python3 ../nesgenie_6to8.py ../test-in/rcproam1.nes nnynnn

echo "=== Super Mario Bros. 3 - YELZUG (should find YEUZUGAA) ==="
python3 ../nesgenie_6to8.py ../test-in/smb3.nes yelzug
echo

echo "=== SMB 1 - AAAAAA (should print a warning) ==="
python3 ../nesgenie_6to8.py ../test-in/smb1.nes aaaaaa
echo

echo "=== These should cause three errors ==="
python3 ../nesgenie_6to8.py ../test-in/smb1.nes       dddddd
python3 ../nesgenie_6to8.py ../test-in/smb1.nes       eaeaeaea
python3 ../nesgenie_6to8.py ../test-in/invalid-id.nes aaaaaa
echo
