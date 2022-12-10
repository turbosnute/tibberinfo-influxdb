#!/bin/sh

set -aux
cd $(dirname $0)

INTERVAL_SECONDS=${INTERVAL_SECONDS:-43200}
CHECK=`echo "${LOAD_HISTORY:-False}" | tr '[:upper:]' '[:lower:]'`

#echo "CHECK: $CHECK"

if [ "$CHECK" = 'true' ]
then
  echo "Loading history..."
  python3 tibberinfo.py
  echo "History loaded. Now you can run the container without the LOADHISTORY variable..."
else
  while :
  do
    echo "--- Start Call API"
    python3 tibberinfo.py
    RET=$?
    echo "Sleep ${INTERVAL_SECONDS} seconds"
    sleep ${INTERVAL_SECONDS}
  done
fi
