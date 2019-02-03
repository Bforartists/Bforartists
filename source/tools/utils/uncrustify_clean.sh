#!/bin/bash

CFG="source/tools/utils/uncrustify.cfg"

if [ ! -f $CFG ]
then
	echo "Run this from the blender source directory: " $CFG " not found, aborting"
	exit 0
fi


for fn in "$@"
do
	# without this, the script simply undoes whitespace changes.
	uncrustify -c $CFG --no-backup --replace "$fn"

	cp "$fn" "$fn.NEW"
	git checkout "$fn" 1> /dev/null

	diff "$fn" "$fn.NEW" -u --ignore-trailing-space --ignore-blank-lines > "$fn.DIFF"

	patch "$fn" "$fn.DIFF" 1> /dev/null

	rm "$fn.NEW"
	rm "$fn.DIFF"
done
