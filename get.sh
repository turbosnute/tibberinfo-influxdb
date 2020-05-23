#!/bin/bash
CHECK=`echo "$LOAD_HISTORY" | tr '[:upper:]' '[:lower:]'`

#echo "CHECK: $CHECK"

if [ "$CHECK" = 'true' ]
then
  echo "Loading history..."
  python3 tibberinfo.py
  echo "History loaded. Now you can run the container without the LOADHISTORY variable..."
else
  while :
  do
    #date
    echo "--- Start Call API"
    python3 tibberinfo.py
    RET=$?
    #date
    echo "Sleep 1 min"
    sleep 60
  done
fi
