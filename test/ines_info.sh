clear

for file in ../test-in/*.nes
do
    python3 ../ines_info.py $file
done
