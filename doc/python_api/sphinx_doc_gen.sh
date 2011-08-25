#!/bin/sh
# run from the blender source dir
#   bash source/blender/python/doc/sphinx_doc_gen.sh
# ssh upload means you need an account on the server


# ----------------------------------------------------------------------------
# Upload vars

# disable for testing
DO_UPLOAD=true

BLENDER="./blender.bin"
SSH_USER="ideasman42"
SSH_HOST=$SSH_USER"@emo.blender.org"
SSH_UPLOAD="/data/www/vhosts/www.blender.org/documentation" # blender_python_api_VERSION, added after

# ----------------------------------------------------------------------------
# Blender Version & Info

# 'Blender 2.53 (sub 1) Build' --> '2_53_1' as a shell script.
# "_".join(str(v) for v in bpy.app.version)
# custom blender vars
blender_srcdir=$(dirname $0)/../../
blender_version=$(grep "BLENDER_VERSION\s" $blender_srcdir/source/blender/blenkernel/BKE_blender.h | awk '{print $3}')
blender_version_char=$(grep BLENDER_VERSION_CHAR $blender_srcdir/source/blender/blenkernel/BKE_blender.h | awk '{print $3}')
blender_version_cycle=$(grep BLENDER_VERSION_CYCLE $blender_srcdir/source/blender/blenkernel/BKE_blender.h | awk '{print $3}')
blender_subversion=$(grep BLENDER_SUBVERSION $blender_srcdir/source/blender/blenkernel/BKE_blender.h | awk '{print $3}')

if [ "$blender_version_cycle" == "release" ]
then
	BLENDER_VERSION=$(expr $blender_version / 100)_$(expr $blender_version % 100)$blender_version_char"_release"
else
	BLENDER_VERSION=$(expr $blender_version / 100)_$(expr $blender_version % 100)_$blender_subversion
fi

SSH_UPLOAD_FULL=$SSH_UPLOAD/"blender_python_api_"$BLENDER_VERSION

SPHINXBASE=doc/python_api/


# ----------------------------------------------------------------------------
# Generate reStructuredText (blender/python only)

# dont delete existing docs, now partial updates are used for quick builds.
$BLENDER --background --factory-startup --python $SPHINXBASE/sphinx_doc_gen.py


# ----------------------------------------------------------------------------
# Generate HTML (sphinx)

sphinx-build -n -b html $SPHINXBASE/sphinx-in $SPHINXBASE/sphinx-out


# ----------------------------------------------------------------------------
# Generate PDF (sphinx/laytex)

sphinx-build -n -b latex $SPHINXBASE/sphinx-in $SPHINXBASE/sphinx-out
make -C $SPHINXBASE/sphinx-out
mv $SPHINXBASE/sphinx-out/contents.pdf $SPHINXBASE/sphinx-out/blender_python_reference_$BLENDER_VERSION.pdf

# ----------------------------------------------------------------------------
# Upload to blender servers, comment this section for testing

if $DO_UPLOAD ; then

	cp $SPHINXBASE/sphinx-out/contents.html $SPHINXBASE/sphinx-out/index.html
	ssh $SSH_USER@emo.blender.org 'rm -rf '$SSH_UPLOAD_FULL'/*'
	rsync --progress -avze "ssh -p 22" $SPHINXBASE/sphinx-out/* $SSH_HOST:$SSH_UPLOAD_FULL/

	## symlink the dir to a static URL
	#ssh $SSH_USER@emo.blender.org 'rm '$SSH_UPLOAD'/250PythonDoc && ln -s '$SSH_UPLOAD_FULL' '$SSH_UPLOAD'/250PythonDoc'

	# better redirect
	ssh $SSH_USER@emo.blender.org 'echo "<html><head><title>Redirecting...</title><meta http-equiv=\"REFRESH\" content=\"0;url=../blender_python_api_'$BLENDER_VERSION'/\"></head><body>Redirecting...</body></html>" > '$SSH_UPLOAD'/250PythonDoc/index.html'

	# rename so local PDF has matching name.
	rsync --progress -avze "ssh -p 22" $SPHINXBASE/sphinx-out/blender_python_reference_$BLENDER_VERSION.pdf $SSH_HOST:$SSH_UPLOAD_FULL/blender_python_reference_$BLENDER_VERSION.pdf

fi


# ----------------------------------------------------------------------------
# Print some useful text

echo ""
echo "Finished! view the docs from: "
echo "  html:" $SPHINXBASE/sphinx-out/contents.html
echo "   pdf:" $SPHINXBASE/sphinx-out/blender_python_reference_$BLENDER_VERSION.pdf
