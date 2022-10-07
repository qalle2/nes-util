clear

echo "=== Excitebike: US code SXZTYU to 15-in-1 multicart (should find SXXTYUVV) ==="
python3 ../nesgenie_verconv.py sxztyu ../test-in/excitebike.nes ../test-in/15in1.nes
echo

echo "=== Excitebike: 15-in-1 multicart code SXXTYUVV to US (should find SXZTYU) ==="
python3 ../nesgenie_verconv.py sxxtyuvv ../test-in/15in1.nes ../test-in/excitebike.nes
echo

echo "=== Journey to Silius: XTUSKTAV, US->EUR (should find XTVSNTAV) ==="
python3 ../nesgenie_verconv.py \
    xtusktav ../test-in/journey.nes ../test-in/journey-e.nes
echo

echo "=== Journey to Silius: XTUSKTAV, US->EUR, -s1 (should find XTVSNTAV) ==="
python3 ../nesgenie_verconv.py \
    xtusktav -s 1 ../test-in/journey.nes ../test-in/journey-e.nes
echo

echo "=== Journey to Silius: XTUSKTAV, US->EUR, -d6 (should find XTVSNTAV) ==="
python3 ../nesgenie_verconv.py \
    xtusktav -d 6 ../test-in/journey.nes ../test-in/journey-e.nes
echo

echo "=== Journey to Silius: TEXINTIA, US->EUR (should find TESSXTIA) ==="
python3 ../nesgenie_verconv.py \
    texintia ../test-in/journey.nes ../test-in/journey-e.nes
echo

echo "=== Journey to Silius: TESSXTIA, EUR->US (should find TEXINTIA) ==="
python3 ../nesgenie_verconv.py \
    tessxtia ../test-in/journey-e.nes ../test-in/journey.nes
echo

echo "=== SMB: SXIOPO, US->US, verbose (should find SXIOPO) ==="
python3 ../nesgenie_verconv.py \
    -v sxiopo ../test-in/smb1.nes ../test-in/smb1.nes
echo

echo "=== SMB: NYAAAE (8000:ff), US->US (should find NYAAAE) ==="
python3 ../nesgenie_verconv.py nyaaae ../test-in/smb1.nes ../test-in/smb1.nes
echo

echo "=== SMB: AEYNNY (ffff:00), US->US (should find AEYNNY) ==="
python3 ../nesgenie_verconv.py aeynny ../test-in/smb1.nes ../test-in/smb1.nes
echo

echo "=== SMB 3: SLXPLOVS, US->JP, verbose (should find SLUPGOVS) ==="
python3 ../nesgenie_verconv.py \
    -v slxplovs ../test-in/smb3.nes ../test-in/smb3-j.nes
echo

echo "=== SMB 3: YEUZUGAA, US->JP, verbose (should find YEUZUGAA) ==="
python3 ../nesgenie_verconv.py \
    -v yeuzugaa ../test-in/smb3.nes ../test-in/smb3-j.nes
echo

echo "=== These should cause six errors ==="
python3 ../nesgenie_verconv.py \
    dapapa ../test-in/smb1.nes ../test-in/smb1.nes
python3 ../nesgenie_verconv.py \
    aaaaaa ../test-in/invalid-id.nes ../test-in/smb1.nes
python3 ../nesgenie_verconv.py \
    aaaaaa ../test-in/smb1.nes ../test-in/invalid-id.nes
python3 ../nesgenie_verconv.py \
    yelzug ../test-in/smb3.nes ../test-in/smb3-j.nes
python3 ../nesgenie_verconv.py \
    paeaaaza ../test-in/smb3.nes ../test-in/smb1.nes
python3 ../nesgenie_verconv.py \
    yeuzugaa ../test-in/smb3.nes ../test-in/smb1.nes
echo
