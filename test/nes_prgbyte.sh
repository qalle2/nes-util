clear

echo "=== SMB 1 (0000, 7fff) ==="
python3 ../nes_prgbyte.py ../test-in/smb1.nes 0000
python3 ../nes_prgbyte.py ../test-in/smb1.nes 7fff
echo

echo "=== This should cause an error ==="
python3 ../nes_prgbyte.py ../test-in/smb1.nes 8000
echo
