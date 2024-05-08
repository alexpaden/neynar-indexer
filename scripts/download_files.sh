#!/bin/bash
lockfile=/tmp/download_files.lock
if [ -e ${lockfile} ] && kill -0 `cat ${lockfile}`; then
    echo "Download files script already running"
    exit
fi

# Make sure the lockfile is removed when we exit and then claim it
trap "rm -f ${lockfile}; exit" INT TERM EXIT
echo $$ > ${lockfile}

# Execute the Python script
python3 download_or_update_files.py

rm -f ${lockfile}