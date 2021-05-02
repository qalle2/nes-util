clear

echo "=== SMB 1 (0000, 7fff) ==="
python3 ../nes_cpuaddr.py ../test-in/smb1.nes 0000
python3 ../nes_cpuaddr.py ../test-in/smb1.nes 7fff
echo

echo "=== Blaster Master (0000, 1ffff) ==="
python3 ../nes_cpuaddr.py ../test-in/blastermaster.nes 0000
python3 ../nes_cpuaddr.py ../test-in/blastermaster.nes 1ffff
echo

echo "=== SMB 3 (0000, 3ffff) ==="
python3 ../nes_cpuaddr.py ../test-in/smb3.nes 0000
python3 ../nes_cpuaddr.py ../test-in/smb3.nes 3ffff
echo

echo "=== Videomation (0000; should warn about unknown mapper) ==="
python3 ../nes_cpuaddr.py ../test-in/videomation.nes 0000
echo

echo "=== This should cause an error ==="
python3 ../nes_cpuaddr.py ../test-in/smb1.nes 8000
echo
