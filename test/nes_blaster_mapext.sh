clear

rm -f ../test-out/*.nes
rm -f ../test-out/*.png

echo "=== Default settings, US ==="
python3 ../nes_blaster_mapext.py -m ../test-out/default.png ../test-in/blastermaster.nes
echo

echo "=== USB/SB/blocks (no map) of map 0, US, verbose ==="
python3 ../nes_blaster_mapext.py -v -u ../test-out/usb0.png -s ../test-out/sb0.png -b ../test-out/blocks0.png ../test-in/blastermaster.nes
echo

echo "=== USB/SB/blocks (no map) of map 8, US ==="
python3 ../nes_blaster_mapext.py -n8 -u ../test-out/usb8.png -s ../test-out/sb8.png -b ../test-out/blocks8.png ../test-in/blastermaster.nes
echo

echo "=== All maps, map only, US ==="
for ((i = 0; i < 16; i++))
do
    python3 ../nes_blaster_mapext.py -n$i -m ../test-out/map$i.png ../test-in/blastermaster.nes
done
echo

echo "=== Map 9, map only, Japanese ==="
python3 ../nes_blaster_mapext.py -j -n9 -m ../test-out/map9j.png ../test-in/blastermaster-j.nes
echo

echo "=== These should cause five errors/warnings ==="
echo
python3 ../nes_blaster_mapext.py ../test-in/nonexistent.nes
python3 ../nes_blaster_mapext.py -m ../test-out/default.png ../test-in/blastermaster.nes
python3 ../nes_blaster_mapext.py ../test-in/blastermaster.nes
echo
python3 ../nes_blaster_mapext.py -n9 -m ../test-out/error1.png ../test-in/blastermaster-j.nes
echo
python3 ../nes_blaster_mapext.py -j -n9 -m ../test-out/error2.png ../test-in/blastermaster.nes
echo
