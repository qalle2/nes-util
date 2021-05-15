clear

python3 ../ines_info.py ../test-in/smb1.nes
echo

for file in ../test-in/*.nes
do
    python3 ../ines_info.py -c $file
done
echo
