clear

rm -f ../test-out/*.png

echo "=== Decoding iNES ROM files ==="
python3 ../nes_chr_decode.py ../test-in/smb1.nes          ../test-out/smb1-chr1.png
python3 ../nes_chr_decode.py ../test-in/blastermaster.nes ../test-out/blastermaster-chr1.png
echo

echo "=== Decoding raw CHR data files ==="
python3 ../nes_chr_decode.py                                       ../test-in/smb1.chr          ../test-out/smb1-chr2.png
python3 ../nes_chr_decode.py --palette 0000ff ff0000 ff00ff ffff00 ../test-in/smb1.chr          ../test-out/smb1-chr3.png
python3 ../nes_chr_decode.py                                       ../test-in/blastermaster.chr ../test-out/blastermaster-chr2.png
python3 ../nes_chr_decode.py                                       ../test-in/chr-2color.chr    ../test-out/chr-2color.png
echo

echo "=== These should cause three errors ==="
python3 ../nes_chr_decode.py --palette 000000 111111 222222 33333  ../test-in/smb1.chr  ../test-out/invalid1.png
python3 ../nes_chr_decode.py --palette 000000 111111 222222 33333g ../test-in/smb1.chr  ../test-out/invalid2.png
python3 ../nes_chr_decode.py                                       ../test-in/empty.chr ../test-out/invalid4.png
echo

echo "=== Verify the decoded files yourself ==="
echo
