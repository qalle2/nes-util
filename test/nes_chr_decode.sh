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
    ../test-in/smb1.chr ../test-out/smb1-chr3.png 0000ff,ff0000,ff00ff,ffff00
python3 ../nes_chr_decode.py \
    ../test-in/blastermaster.chr ../test-out/blastermaster-chr2.png
python3 ../nes_chr_decode.py \
    ../test-in/chr-2color.chr ../test-out/chr-2color.png
echo

echo "=== Verifying (different PNG encoding may give false positives) ==="
md5sum -c --quiet nes_chr_decode.md5
echo

echo "=== These should cause six errors ==="
python3 ../nes_chr_decode.py \
    ../test-in/smb1.chr ../test-out/test1.png 000000,111111,222222
python3 ../nes_chr_decode.py \
    ../test-in/smb1.chr ../test-out/test2.png 000000,111111,222222,x
python3 ../nes_chr_decode.py \
    ../test-in/smb1.chr ../test-out/test3.png 000000,111111,222222,1234567
python3 ../nes_chr_decode.py \
    ../test-in/invalid-id.nes ../test-out/test4.png
python3 ../nes_chr_decode.py \
    ../test-in/empty.chr ../test-out/test5.png
python3 ../nes_chr_decode.py \
    ../test-in/videomation.nes ../test-out/test6.png
echo
