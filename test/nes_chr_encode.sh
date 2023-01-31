clear
rm -f ../test-out/*.chr

echo "=== Encoding ==="
python3 ../nes_chr_encode.py \
    ../test-in/smb1-chr.png ../test-out/smb1a.chr
python3 ../nes_chr_encode.py \
    ../test-in/smb1-chr-grayscale.png ../test-out/smb1b.chr
python3 ../nes_chr_encode.py \
    ../test-in/smb1-chr-rgb.png ../test-out/smb1c.chr
python3 ../nes_chr_encode.py \
    ../test-in/smb1-chr-rgba.png ../test-out/smb1d.chr
python3 ../nes_chr_encode.py \
    ../test-in/smb1-chr-altcolor.png ../test-out/smb1e.chr \
    0000ff,ff0000,ff00ff,00ff00
python3 ../nes_chr_encode.py \
    ../test-in/smb1-chr.gif ../test-out/smb1f.chr
python3 ../nes_chr_encode.py \
    ../test-in/blastermaster-chr.png ../test-out/blastermaster.chr
python3 ../nes_chr_encode.py \
    ../test-in/chr-1color.png ../test-out/chr-1color.chr
python3 ../nes_chr_encode.py \
    ../test-in/chr-2color.png ../test-out/chr-2color.chr
echo

echo "=== Verifying ==="
md5sum -c --quiet nes_chr_encode.md5
echo

echo "=== These should cause six errors ==="
python3 ../nes_chr_encode.py \
    ../test-in/smb1-chr.png ../test-out/test1.chr \
    000000,111111,222222
python3 ../nes_chr_encode.py \
    ../test-in/smb1-chr.png ../test-out/test2.chr \
    000000,111111,222222,1234567
python3 ../nes_chr_encode.py \
    ../test-in/smb1-chr.png ../test-out/test3.chr \
    000000,111111,222222,x
python3 ../nes_chr_encode.py \
    ../test-in/smb1-chr.png ../test-out/test4.chr \
    000000,111111,222222,000000
python3 ../nes_chr_encode.py \
    ../test-in/smb1-chr.png ../test-out/test5.chr \
    000000,696969,420420,ffffff
python3 ../nes_chr_encode.py \
    ../test-in/5colors.png ../test-out/test6.chr
echo
