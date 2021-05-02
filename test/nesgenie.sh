clear

echo "=== These should print the same text four times ==="
python3 ../nesgenie.py sxiopo
python3 ../nesgenie.py sxsopo
python3 ../nesgenie.py 91d9 ad
python3 ../nesgenie.py 11d9 ad
echo

echo "=== These should print the same text four times ==="
python3 ../nesgenie.py yeuzugaa
python3 ../nesgenie.py yelzugaa
python3 ../nesgenie.py acb3 07 00
python3 ../nesgenie.py 2cb3 07 00
echo

echo "=== These should cause three errors ==="
python3 ../nesgenie.py cccccc
python3 ../nesgenie.py fffg ff
python3 ../nesgenie.py 10000 00 00
echo
