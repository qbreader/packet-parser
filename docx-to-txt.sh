#!/bin/bash

TYPE=docx

mkdir -p packets
echo "Parsing ${TYPE} to text..."
counter=0
for filename in p-$TYPE/*.$TYPE; do
    echo "Parsing ${filename}..."
    counter=$((counter+1))
    BASENAME=$(echo "${filename}" | cut -d'/' -f 2)
    python3 docx-to-txt.py "${filename}" > "packets/${BASENAME%.docx}.txt"
done
echo "Parsed ${counter} ${TYPE}s."
