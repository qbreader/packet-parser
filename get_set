#!/bin/bash

URL="quizbowlpackets.com/"

while getopts 'cmt' flag; do
    case "${flag}" in
        c) URL="collegiate.quizbowlpackets.com/" ;;
        m) URL="ms.quizbowlpackets.com/" ;;
        t) URL="trash.quizbowlpackets.com/" ;;
    esac
done

read -p "Set ID (number after ${URL}): " SET
wget robots=off -nv -A.pdf --include-directories=$SET -r "https://${URL}"
mv "${URL}${SET}/" ".packets-pdf"
rm -r "${URL}"
mkdir -p "packets"

echo "Parsing PDFs to text..."
counter=0
for filename in .packets-pdf/*.pdf; do
    counter=$((counter+1))
    pdftotext -q -layout "$filename" "packets/${counter}.txt"
done
rm -r .packets-pdf
echo "Parsed ${counter} PDFs."

echo "Parsing text to json..."
rm -fr output
python3 parser.py
echo "Done."