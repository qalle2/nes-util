clear
rm -f ../test-out/*.nes

echo "=== Swapping colors ==="
python3 ../nes_color_swap.py \
    ../test-in/smb1.nes ../test-out/smb1-default_settings.nes
python3 ../nes_color_swap.py \
    -c 0 1 2 3 ../test-in/smb1.nes ../test-out/smb1-colors0123.nes
python3 ../nes_color_swap.py \
    -c 0 2 3 1 -n 492 ../test-in/smb1.nes ../test-out/smb1-colors0231.nes
python3 ../nes_color_swap.py \
    -c 0 3 1 2 -n 492 ../test-in/smb1.nes ../test-out/smb1-colors0312.nes
python3 ../nes_color_swap.py \
    -c 1 2 3 2 -n 492 ../test-in/smb1.nes ../test-out/smb1-colors1232.nes
python3 ../nes_color_swap.py \
    -c 1 2 3 0 -n 1 ../test-in/smb1.nes ../test-out/smb1-tile_0_only.nes
python3 ../nes_color_swap.py \
    -c 1 2 3 0 -f 1 -n 1 ../test-in/smb1.nes ../test-out/smb1-tile_1_only.nes
python3 ../nes_color_swap.py \
    -c 1 2 3 0 -f 511 ../test-in/smb1.nes ../test-out/smb1-tile_511_only.nes
python3 ../nes_color_swap.py \
    ../test-in/blastermaster.nes ../test-out/blastermaster-colors0231.nes
python3 ../nes_color_swap.py \
    -c 0 1 2 3 ../test-in/blastermaster.nes \
    ../test-out/blastermaster-colors0123.nes
echo

echo "=== Validating ==="
cd ../test-out/
md5sum -c --quiet ../test/nes_color_swap.md5
cd ../test/
echo

rm -f ../test-out/*.nes
echo "" > ../test-out/already-exists.nes

echo "=== These should cause seven errors ==="
python3 ../nes_color_swap.py -f 512 ../test-in/smb1.nes ../test-out/test1.nes
python3 ../nes_color_swap.py -n 513 ../test-in/smb1.nes ../test-out/test2.nes
python3 ../nes_color_swap.py \
    -f 511 -n 2 ../test-in/smb1.nes ../test-out/test3.nes
python3 ../nes_color_swap.py nonexistent ../test-out/test4.nes
python3 ../nes_color_swap.py ../test-in/smb1.nes ../test-out/already-exists.nes
python3 ../nes_color_swap.py ../test-in/invalid-id.nes ../test-out/test5.nes
python3 ../nes_color_swap.py ../test-in/videomation.nes ../test-out/test6.nes
echo
