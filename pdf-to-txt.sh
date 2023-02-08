#!/bin/bash

TYPE=pdf

mkdir -p packets
echo "Parsing ${TYPE} to text..."
counter=0
for filename in p-$TYPE/*.$TYPE; do
    echo "Parsing ${filename}..."
    counter=$((counter+1))
    BASENAME=$(echo "${filename}" | cut -d'/' -f 2)
    case $TYPE in
        pdf) python3 pdf-to-docx.py "$filename" && python3 docx-to-txt.py "${filename%.pdf}.docx" > "packets/${BASENAME%.pdf}.txt";;
        docx) python3 docx-to-txt.py "${filename}" > "packets/${BASENAME%.docx}.txt" ;;
        txt) mv "$filename" "packets/${BASENAME%.txt}.txt" ;;
    esac
done
rm -r p-$TYPE
echo "Parsed ${counter} ${TYPE}s."

echo "Parsing text to json..."
rm -fr output
case $TYPE in
    pdf) python3 packet-parser.py -f ;;
    docx) python3 packet-parser.py -f ;;
    txt) python3 packet-parser.py ;;
esac
echo "Done."
