clear

echo "=== SMB 1 (should print 0x78, 0xff) ==="
python3 ../nes_prgbyte.py ../test-in/smb1.nes 0000
python3 ../nes_prgbyte.py ../test-in/smb1.nes 7fff
echo

echo "=== These should cause two errors ==="
python3 ../nes_prgbyte.py ../test-in/smb1.nes -1
python3 ../nes_prgbyte.py ../test-in/smb1.nes 8000
echo
