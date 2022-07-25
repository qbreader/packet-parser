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
mkdir -p "answerline-formatting"

##### Convert all files to .txt, and for .docx and .pdf also get the answerline formatting #####
echo "Parsing ${TYPE} to text..."
counter=0
for filename in .packets-$TYPE/*.$TYPE; do
    echo "Parsing ${filename}..."
    counter=$((counter+1))
    case $TYPE in
        pdf) pdftotext -q -layout "$filename" "packets/${counter}.txt" && python pdf-to-docx.py "$filename" && python docx-to-txt.py "${filename%.pdf}.docx" > "answerline-formatting/${counter}.txt";;
        docx) docx2txt "$filename" && mv "${filename%.docx}.txt" "packets/${counter}.txt" && python3 docx-to-txt.py "${filename}" > "answerline-formatting/${counter}.txt" ;;
        txt) mv "$filename" "packets/${counter}.txt" ;;
    esac
done
rm -r .packets-$TYPE
echo "Parsed ${counter} ${TYPE}s."

echo "Parsing text to json..."
rm -fr output
python3 parser.py
echo "Done."