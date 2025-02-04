#!/bin/sh

set -aux
cd $(dirname $0)

INTERVAL_SECONDS=${INTERVAL_SECONDS:-43200}

while :
do
  echo "--- Start Call API"
  python3 tibberinfo.py --verbose
  RET=$?
  echo "Sleep ${INTERVAL_SECONDS} seconds"
  sleep ${INTERVAL_SECONDS}
done
