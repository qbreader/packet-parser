#!/bin/bash

source download-set.sh

if [ $TYPE == "doc" ]; then
    exit 0;
fi

source to-txt.sh

echo "Parsing text to json..."
rm -r p-$TYPE
rm -fr output
case $TYPE in
    pdf) python3 packet-parser.py -f ;;
    docx) python3 packet-parser.py -f ;;
    txt) python3 packet-parser.py ;;
esac
echo "Done."
