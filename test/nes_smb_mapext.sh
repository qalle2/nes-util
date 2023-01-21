clear
rm -f ../test-out/*.png

for ((i = 0; i < 3; i++)); do
    python3 ../nes_smb_mapext.py \
        ../test-in/smb1.nes ../test-out/area0-$i.png 0 $i
done

for ((i = 0; i < 22; i++)); do
    python3 ../nes_smb_mapext.py \
        ../test-in/smb1.nes ../test-out/area1-$i.png 1 $i
done

for ((i = 0; i < 3; i++)); do
    python3 ../nes_smb_mapext.py \
        ../test-in/smb1.nes ../test-out/area2-$i.png 2 $i
done

for ((i = 0; i < 6; i++)); do
    python3 ../nes_smb_mapext.py \
        ../test-in/smb1.nes ../test-out/area3-$i.png 3 $i
done
