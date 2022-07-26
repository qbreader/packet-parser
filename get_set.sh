#!/bin/bash

URL="quizbowlpackets.com/"

while getopts 'cmt' flag; do
    case "${flag}" in
        c) URL="collegiate.quizbowlpackets.com/" ;;
        m) URL="ms.quizbowlpackets.com/" ;;
        t) URL="trash.quizbowlpackets.com/" ;;
    esac
done

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
    BASENAME=$(echo "${filename%.pdf}" | cut -d'/' -f 2)
    case $TYPE in
        pdf) python pdf-to-docx.py "$filename" && python docx-to-txt.py "${filename%.pdf}.docx" > "packets/${BASENAME}.txt";;
        docx) python3 docx-to-txt.py "${filename}" > "packets/${BASENAME}.txt" ;;
        txt) mv "$filename" "packets/${BASENAME}.txt" ;;
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
echo "Make sure to check the packets for any artifacts, such as the \":\" character at the beginning of answers."