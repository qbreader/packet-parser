#!/bin/bash

URL="quizbowlpackets.com/"

read -p "Packet level (m = middle school, c = college, t/p = trash; leave blank for high school): " LEVEL
case $LEVEL in
    c) URL="collegiate.quizbowlpackets.com/" ;;
    m) URL="ms.quizbowlpackets.com/" ;;
    t | p) URL="popculture.quizbowlpackets.com/" ;;
esac

##### Download all packets in the set to folder called p-TYPE #####
read -p "Set ID (number after ${URL}): " SET
read -p "File type (p = pdf, d = docx, c = doc): " TYPE
case $TYPE in
    p | pdf) TYPE="pdf" ;;
    d | docx) TYPE="docx" ;;
    c | doc) TYPE="doc" ;;
    t | txt) TYPE="txt" ;;
    *) echo "Invalid file type" && exit 1 ;;
esac
echo "Getting packets from ${URL}${SET}"
wget -nv -A.$TYPE -r --span-hosts --domains=$URL,"files.quizbowlpackets.com" "https://${URL}/${SET}/"
mv "files.quizbowlpackets.com/${SET}" "p-$TYPE"
rm -r "files.quizbowlpackets.com"
rm -r $URL
