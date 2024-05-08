#!/bin/bash
lockfile=/tmp/update_full_files.lock
if [ -e ${lockfile} ] && kill -0 `cat ${lockfile}`; then
    echo "Update full files script already running"
    exit
fi

# Make sure the lockfile is removed when we exit and then claim it
trap "rm -f ${lockfile}; exit" INT TERM EXIT
echo $$ > ${lockfile}

# Delay execution for 24 hours
sleep 86400

# Execute the Python script
python3 update_full_files.py

rm -f ${lockfile}
