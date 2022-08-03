#!/bin/bash

URL="quizbowlpackets.com/"

read -p "Packet level (m = middle school, c = college, t = trash; leave blank for high school): " LEVEL
case $LEVEL in
    c) URL="collegiate.quizbowlpackets.com/" ;;
    m) URL="ms.quizbowlpackets.com/" ;;
    t) URL="trash.quizbowlpackets.com/" ;;
esac

##### Download all packets in the set #####
read -p "Set ID (number after ${URL}): " SET
read -p "File type (p = pdf, d = docx): " TYPE
case $TYPE in
    p | pdf) TYPE="pdf" ;;
    d | docx) TYPE="docx" ;;
    t | txt) TYPE="txt" ;;
    *) echo "Invalid file type" && exit 1 ;;
esac
echo "Getting packets from ${URL}${SET}"
wget robots=off -nv -A.$TYPE --include-directories=$SET -r "https://${URL}"
mv "${URL}${SET}/" ".packets-$TYPE"
rm -r "${URL}"
mkdir -p "packets"

##### Convert all files to .txt, and for .docx and .pdf also get the answerline formatting #####
echo "Parsing ${TYPE} to text..."
counter=0
for filename in .packets-$TYPE/*.$TYPE; do
    echo "Parsing ${filename}..."
    counter=$((counter+1))
    BASENAME=$(echo "${filename}" | cut -d'/' -f 2)
    case $TYPE in
        pdf) python3 pdf-to-docx.py "$filename" && python3 docx-to-txt.py "${filename%.pdf}.docx" > "packets/${BASENAME%.pdf}.txt";;
        docx) python3 docx-to-txt.py "${filename}" > "packets/${BASENAME%.docx}.txt" ;;
        txt) mv "$filename" "packets/${BASENAME%.txt}.txt" ;;
    esac
done
rm -r .packets-$TYPE
echo "Parsed ${counter} ${TYPE}s."

echo "Parsing text to json..."
rm -fr output
case $TYPE in
    pdf) python3 parser.py -f ;;
    docx) python3 parser.py -f ;;
    txt) python3 parser.py ;;
esac
echo "Done."