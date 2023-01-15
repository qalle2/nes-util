clear

echo "=== Should print SXIOPO twice and YEUZUGAA twice ==="
python3 ../nesgenie_enc.py 91d9 ad
python3 ../nesgenie_enc.py 11d9 ad
python3 ../nesgenie_enc.py acb3 07 00
python3 ../nesgenie_enc.py 2cb3 07 00
echo

echo "=== Should print 91d9/ad/none twice and acb3/07/00 twice ==="
python3 ../nesgenie_dec.py sxiopo
python3 ../nesgenie_dec.py sxsopo
python3 ../nesgenie_dec.py yeuzugaa
python3 ../nesgenie_dec.py yelzugaa
echo

echo "=== These should cause four errors ==="
python3 ../nesgenie_dec.py cccccc
python3 ../nesgenie_dec.py apzlgit
python3 ../nesgenie_enc.py fffg ff
python3 ../nesgenie_enc.py 10000 00 00
echo
