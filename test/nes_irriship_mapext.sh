clear
rm -f ../test-out/*.png

echo "=== Running ==="
python3 ../nes_irriship_mapext.py \
    ../test-in/irriship.nes ../test-out/irriship.png
echo

echo "=== Verifying (different PNG encoding may give false positives) ==="
md5sum -c --quiet nes_irriship_mapext.md5
echo
