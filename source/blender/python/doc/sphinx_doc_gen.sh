#!/bin/sh
# run from the blender source dir
#   bash source/blender/python/doc/sphinx_doc_gen.sh
# ssh upload means you need an account on the server

BLENDER="./blender.bin"
SSH_HOST="ideasman42@emo.blender.org"
SSH_UPLOAD="/data/www/vhosts/www.blender.org/documentation" # blender_python_api_VERSION, added after

# sed string from hell, 'Blender 2.53 (sub 1) Build' --> '2_53_1'
# "_".join(str(v) for v in bpy.app.version)
BLENDER_VERSION=`$BLENDER --version | cut -f2-4 -d" " | sed 's/(//g' | sed 's/)//g' | sed 's/ sub /./g' | sed 's/\./_/g'`
SSH_UPLOAD_FULL=$SSH_UPLOAD/"blender_python_api_"$BLENDER_VERSION

# dont delete existing docs, now partial updates are used for quick builds.
$BLENDER --background --python ./source/blender/python/doc/sphinx_doc_gen.py

# html
sphinx-build source/blender/python/doc/sphinx-in source/blender/python/doc/sphinx-out
cp source/blender/python/doc/sphinx-out/contents.html source/blender/python/doc/sphinx-out/index.html
ssh ideasman42@emo.blender.org 'rm -rf '$SSH_UPLOAD_FULL'/*'
rsync --progress -avze "ssh -p 22" /b/source/blender/python/doc/sphinx-out/* $SSH_HOST:$SSH_UPLOAD_FULL/

# pdf
sphinx-build -b latex source/blender/python/doc/sphinx-in source/blender/python/doc/sphinx-out
cd source/blender/python/doc/sphinx-out
make
cd ../../../../../
rsync --progress -avze "ssh -p 22" source/blender/python/doc/sphinx-out/contents.pdf $SSH_HOST:$SSH_UPLOAD_FULL/blender_python_reference_$BLENDER_VERSION.pdf
