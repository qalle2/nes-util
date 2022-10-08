clear
rm -f ../test-out/*.nes

echo "=== These should cause four errors ==="
python3 ../nes_color_swap.py -f 9999 ../test-in/smb1.nes        ../test-out/invalid1.nes
python3 ../nes_color_swap.py -n 9999 ../test-in/smb1.nes        ../test-out/invalid2.nes
python3 ../nes_color_swap.py                   ../test-in/invalid-id.nes  ../test-out/invalid3.nes
python3 ../nes_color_swap.py                   ../test-in/videomation.nes ../test-out/invalid4.nes
echo

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

echo "=== Comparing ==="
echo "Should be identical:"
diff -q ../test-in/smb1.nes          ../test-out/smb1-colors0123.nes
diff -q ../test-in/blastermaster.nes ../test-out/blastermaster-colors0123.nes
echo "Only tile 0 changed:"
diff \
    <(od -Ax -tx1 -v ../test-in/smb1.nes) \
    <(od -Ax -tx1 -v ../test-out/smb1-tile_0_only.nes) \
    | grep "^[<>]"
echo "Only tile 1 changed:"
diff \
    <(od -Ax -tx1 -v ../test-in/smb1.nes) \
    <(od -Ax -tx1 -v ../test-out/smb1-tile_1_only.nes) \
    | grep "^[<>]"
echo "Only tile 511 changed:"
diff \
    <(od -Ax -tx1 -v ../test-in/smb1.nes) \
    <(od -Ax -tx1 -v ../test-out/smb1-tile_511_only.nes) \
    | grep "^[<>]"
echo

echo "=== Verify these files yourself ==="
ls -1 ../test-out/*.nes
echo
