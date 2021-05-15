clear

rm -f ../test-out/*.chr

echo "=== Encoding ==="
python3 ../nes_chr_encode.py                                ../test-in/smb1-chr.png           ../test-out/smb1a.chr
python3 ../nes_chr_encode.py                                ../test-in/smb1-chr-grayscale.png ../test-out/smb1b.chr
python3 ../nes_chr_encode.py                                ../test-in/smb1-chr-rgb.png       ../test-out/smb1c.chr
python3 ../nes_chr_encode.py                                ../test-in/smb1-chr-rgba.png      ../test-out/smb1d.chr
python3 ../nes_chr_encode.py -p 0000ff ff0000 ff00ff 00ff00 ../test-in/smb1-chr-altcolor.png  ../test-out/smb1e.chr
python3 ../nes_chr_encode.py                                ../test-in/smb1-chr.gif           ../test-out/smb1f.chr
python3 ../nes_chr_encode.py                                ../test-in/blastermaster-chr.png  ../test-out/blastermaster.chr
python3 ../nes_chr_encode.py                                ../test-in/chr-2color.png         ../test-out/chr-2color.chr
echo

echo "=== Verifying ==="
diff -q ../test-in/smb1.chr          ../test-out/smb1a.chr
diff -q ../test-in/smb1.chr          ../test-out/smb1b.chr
diff -q ../test-in/smb1.chr          ../test-out/smb1c.chr
diff -q ../test-in/smb1.chr          ../test-out/smb1d.chr
diff -q ../test-in/smb1.chr          ../test-out/smb1e.chr
diff -q ../test-in/smb1.chr          ../test-out/smb1f.chr
diff -q ../test-in/blastermaster.chr ../test-out/blastermaster.chr
diff -q ../test-in/chr-2color.chr    ../test-out/chr-2color.chr
echo

echo "=== These should cause five errors ==="
python3 ../nes_chr_encode.py --p 000000 111111 222222 33333  ../test-in/smb1-chr.png ../test-out/invalid1.chr
python3 ../nes_chr_encode.py --p 000000 111111 222222 33333g ../test-in/smb1-chr.png ../test-out/invalid2.chr
python3 ../nes_chr_encode.py --p 000000 111111 222222 000000 ../test-in/smb1-chr.png ../test-out/invalid3.chr
python3 ../nes_chr_encode.py --p 000000 696969 420420 ffffff ../test-in/smb1-chr.png ../test-out/invalid4.chr
python3 ../nes_chr_encode.py                                 ../test-in/5colors.png  ../test-out/invalid5.chr
echo

rm -f ../test-out/*.chr
