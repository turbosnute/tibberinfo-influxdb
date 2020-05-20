#!/bin/bash

while :
do
  date
  echo "--- Start Call API"
  python3 tibberinfo.py
  RET=$?
  date
  echo "Sleep 1 min"
  sleep 60
done
