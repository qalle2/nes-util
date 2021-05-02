clear

rm -f ../test-out/*.nes
rm -f ../test-out/*.png

echo "=== Default settings, US ==="
python3 ../nes_blaster_mapext.py -m ../test-out/default.png ../test-in/blastermaster.nes
echo

echo "=== USB/SB/blocks (no map) of map 0, US, verbose ==="
python3 ../nes_blaster_mapext.py -v -u ../test-out/usb0.png -s ../test-out/sb0.png -b ../test-out/blocks0.png ../test-in/blastermaster.nes
echo

echo "=== All maps, map only, US ==="
for ((i = 0; i < 16; i++))
do
    python3 ../nes_blaster_mapext.py -n $i -m ../test-out/map$i.png ../test-in/blastermaster.nes
done
echo

echo "=== All maps, map only, Japanese ==="
for ((i = 0; i < 16; i++))
do
    python3 ../nes_blaster_mapext.py -j -n $i -m ../test-out/map$[i]j.png ../test-in/blastermaster-j.nes
done
echo

echo "=== These should cause four errors ==="
echo
python3 ../nes_blaster_mapext.py ../test-in/nonexistent.nes
python3 ../nes_blaster_mapext.py -m ../test-out/default.png ../test-in/blastermaster.nes
echo
python3 ../nes_blaster_mapext.py -n 9 -m ../test-out/error1.png ../test-in/blastermaster-j.nes
echo
python3 ../nes_blaster_mapext.py -j -n 9 -m ../test-out/error2.png ../test-in/blastermaster.nes
echo
