clear

echo "=== SMB 1 (PRG address = 0/0x7fff) ==="
python3 ../nes_cpuaddr.py ../test-in/smb1.nes 0
python3 ../nes_cpuaddr.py ../test-in/smb1.nes 7fff
echo

echo "=== Blaster Master (PRG address = 0/0x1ffff) ==="
python3 ../nes_cpuaddr.py ../test-in/blastermaster.nes 0
python3 ../nes_cpuaddr.py ../test-in/blastermaster.nes 1ffff
echo

echo "=== SMB 3 (PRG address = 0/0x3ffff) ==="
python3 ../nes_cpuaddr.py ../test-in/smb3.nes 0
python3 ../nes_cpuaddr.py ../test-in/smb3.nes 3ffff
echo

echo "=== Videomation (PRG address = 0; should warn about unknown mapper) ==="
python3 ../nes_cpuaddr.py ../test-in/videomation.nes 0
echo

echo "=== This should cause an error ==="
python3 ../nes_cpuaddr.py ../test-in/smb1.nes 8000
echo
