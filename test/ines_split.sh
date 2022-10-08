clear
rm -f ../test-out/*.prg
rm -f ../test-out/*.chr

echo "=== Splitting ==="
python3 ../ines_split.py \
    -p ../test-out/smb1.prg -c ../test-out/smb1.chr ../test-in/smb1.nes
python3 ../ines_split.py \
    -p ../test-out/blastermaster.prg ../test-in/blastermaster.nes
python3 ../ines_split.py \
    -c ../test-out/blastermaster.chr ../test-in/blastermaster.nes
echo

echo "=== Validating ==="
diff -q ../test-in/smb1.prg          ../test-out/smb1.prg
diff -q ../test-in/smb1.chr          ../test-out/smb1.chr
diff -q ../test-in/blastermaster.prg ../test-out/blastermaster.prg
diff -q ../test-in/blastermaster.chr ../test-out/blastermaster.chr
echo

rm -f ../test-out/*.prg
rm -f ../test-out/*.chr

echo "=== These should cause four errors ==="
python3 ../ines_split.py -p ../test-out/invalid1.prg ../test-in/invalid-id.nes
python3 ../ines_split.py -p ../test-in/smb1.nes      ../test-in/smb1.nes
python3 ../ines_split.py -c ../test-in/smb1.nes      ../test-in/smb1.nes
python3 ../ines_split.py                             ../test-in/smb1.nes
echo
