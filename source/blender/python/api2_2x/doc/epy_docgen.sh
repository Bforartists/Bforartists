# epy_docgen.sh
# generates blender python doc using epydoc
# requires epydoc in your PATH.
# run from the doc directory containing the .py files
# usage:  sh epy_docgen.sh

epydoc -o BPY_API_236 --url "http://www.blender.org" -t API_intro.py \
 -n "Blender" --no-private --no-frames \
$( ls [A-Z]*.py )
