clear
rm -f ../test-out/*.nes

echo "=== Creating iNES files ==="
python3 ../ines_combine.py \
    -p ../test-in/blastermaster.prg -c ../test-in/blastermaster.chr -m 1 -n h \
    ../test-out/blastermaster.nes
python3 ../ines_combine.py \
    -p ../test-in/smb1.prg -c ../test-in/smb1.chr -m 0 -n v \
    ../test-out/smb1.nes
python3 ../ines_combine.py \
    -p ../test-in/videomation.prg -m 13 -n v ../test-out/videomation.nes
python3 ../ines_combine.py \
    -p ../test-in/zelda1.prg -c ../test-in/empty.chr -m 1 -n h -x \
    ../test-out/zelda1.nes
echo

echo "=== Validating iNES files ==="
cd ../test-out/
md5sum -c --quiet ../test/ines_combine.md5
cd ../test/
echo

echo "=== These should cause two errors ==="
python3 ../ines_combine.py \
    -p ../test-in/smb1.nes ../test-out/invalid1.nes
python3 ../ines_combine.py \
    -p ../test-in/smb1.prg -c ../test-in/smb1.nes ../test-out/invalid2.nes
echo
