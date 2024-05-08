#!/bin/bash
lockfile=/tmp/insert_update_sql.lock
if [ -e ${lockfile} ] && kill -0 `cat ${lockfile}`; then
    echo "Insert/update SQL script already running"
    exit
fi

# Make sure the lockfile is removed when we exit and then claim it
trap "rm -f ${lockfile}; exit" INT TERM EXIT
echo $$ > ${lockfile}

# Execute the Python script
python3 insert_or_update_sql.py

rm -f ${lockfile}