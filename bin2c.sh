#!/bin/bash -e
echo "const PROGMEM uint8_t ${1%%.*}[] = {"
od -An -tx1 -w16 $1 | sed -e "s/ /, 0x/g" -e "s/^, /	/" -e "s/$/,/" -e "$ s/,$//"
echo "};"
