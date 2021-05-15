clear

echo "=== SMB 1 ==="
python3 ../ines_info.py ../test-in/smb1.nes
echo

echo "=== SMB 3 ==="
python3 ../ines_info.py ../test-in/smb3.nes
echo

echo "=== Zelda 1 ==="
python3 ../ines_info.py ../test-in/zelda1.nes
echo

echo "=== These should cause three errors ==="
python3 ../ines_info.py nonexistent
python3 ../ines_info.py ../test-in/invalid-id.nes
python3 ../ines_info.py ../test-in/yoshi.nes
echo
