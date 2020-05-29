#!/bin/sh

# This script can run from any location,
# output is created in the $CWD

BASE_DIR="$PWD"

blender_srcdir=$(dirname -- $0)/../..
blender_version=$(grep "BLENDER_VERSION\s" "$blender_srcdir/source/blender/blenkernel/BKE_blender_version.h" | awk '{print $3}')
blender_version_patch=$(grep "BLENDER_VERSION_PATCH\s" "$blender_srcdir/source/blender/blenkernel/BKE_blender_version.h" | awk '{print $3}')
blender_version_cycle=$(grep "BLENDER_VERSION_CYCLE\s" "$blender_srcdir/source/blender/blenkernel/BKE_blender_version.h" | awk '{print $3}')

VERSION=$(expr $blender_version / 100).$(expr $blender_version % 100).$blender_version_patch
if [ "$blender_version_cycle" = "release" ] ; then
  SUBMODULE_EXCLUDE="^\(release/scripts/addons_contrib\)$"
else
  VERSION=$VERSION-$blender_version_cycle
  SUBMODULE_EXCLUDE="^$"  # dummy regex
fi

MANIFEST="blender-$VERSION-manifest.txt"
TARBALL="blender-$VERSION.tar.xz"

cd "$blender_srcdir"

# not so nice, but works
FILTER_FILES_PY=\
"import os, sys; "\
"[print(l[:-1]) for l in sys.stdin.readlines() "\
"if os.path.isfile(l[:-1]) "\
"if os.path.basename(l[:-1]) not in {"\
"'.gitignore', "\
"'.gitmodules', "\
"'.arcconfig', "\
"}"\
"]"

# Build master list
echo -n "Building manifest of files:  \"$BASE_DIR/$MANIFEST\" ..."
git ls-files | python3 -c "$FILTER_FILES_PY" > $BASE_DIR/$MANIFEST

# Enumerate submodules
for lcv in $(git submodule | awk '{print $2}' | grep -v "$SUBMODULE_EXCLUDE"); do
  cd "$BASE_DIR"
  cd "$blender_srcdir/$lcv"
  git ls-files | python3 -c "$FILTER_FILES_PY" | awk '$0="'"$lcv"/'"$0' >> $BASE_DIR/$MANIFEST
  cd "$BASE_DIR"
done
echo "OK"


# Create the tarball
#
# Without owner/group args, extracting the files as root will
# use ownership from the tar archive.
cd "$blender_srcdir"
echo -n "Creating archive:            \"$BASE_DIR/$TARBALL\" ..."
tar \
  --transform "s,^,blender-$VERSION/,g" \
  --use-compress-program="xz -9" \
  --create \
  --file="$BASE_DIR/$TARBALL" \
  --files-from="$BASE_DIR/$MANIFEST" \
  --owner=0 \
  --group=0

echo "OK"


# Create checksum file
cd "$BASE_DIR"
echo -n "Creating checksum:           \"$BASE_DIR/$TARBALL.md5sum\" ..."
md5sum "$TARBALL" > "$TARBALL.md5sum"
echo "OK"


# Cleanup
echo -n "Cleaning up ..."
rm "$BASE_DIR/$MANIFEST"
echo "OK"

echo "Done!"
