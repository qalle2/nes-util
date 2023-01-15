clear
rm -f ../test-out/*.png

echo "=== Decoding iNES ROM files ==="
python3 ../nes_chr_decode.py \
    ../test-in/smb1.nes ../test-out/smb1-chr1.png
python3 ../nes_chr_decode.py \
    ../test-in/blastermaster.nes ../test-out/blastermaster-chr1.png
echo

echo "=== Decoding raw CHR data files ==="
python3 ../nes_chr_decode.py \
    ../test-in/smb1.chr ../test-out/smb1-chr2.png
python3 ../nes_chr_decode.py \
    -p 0000ff ff0000 ff00ff ffff00 ../test-in/smb1.chr \
    ../test-out/smb1-chr3.png
python3 ../nes_chr_decode.py \
    ../test-in/blastermaster.chr ../test-out/blastermaster-chr2.png
python3 ../nes_chr_decode.py \
    ../test-in/chr-2color.chr ../test-out/chr-2color.png
echo

echo "=== Verifying (different PNG encoding may give false positives) ==="
cd ../test-out/
md5sum -c --quiet ../test/nes_chr_decode.md5
cd ../test/
echo

echo "=== These should cause five errors ==="
python3 ../nes_chr_decode.py \
    -p 000000 111111 222222 x ../test-in/smb1.chr ../test-out/invalid1.png
python3 ../nes_chr_decode.py \
    -p 000000 111111 222222 3333333 ../test-in/smb1.chr \
    ../test-out/invalid2.png
python3 ../nes_chr_decode.py \
    ../test-in/invalid-id.nes ../test-out/invalid3.png
python3 ../nes_chr_decode.py \
    ../test-in/empty.chr ../test-out/invalid4.png
python3 ../nes_chr_decode.py \
    ../test-in/videomation.nes ../test-out/invalid5.png
echo
