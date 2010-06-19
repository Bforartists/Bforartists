#!/bin/sh

echo "*** EIGEN2-HG Update utility"
echo "*** This gets a new eigen2-hg tree and adapts it to blenders build structure"
echo "*** Warning! This script will wipe all the header file"

if [ "x$1" = "x--i-really-know-what-im-doing" ] ; then
    echo Proceeding as requested by command line ...
else
    echo "*** Please run again with --i-really-know-what-im-doing ..."
    exit 1
fi

# get the latest revision from repository.
hg clone http://bitbucket.org/eigen/eigen2
if [ -d eigen2 ]
then
    cd eigen2
    # put here the version you want to use
    hg up 2.0
    rm -f `find Eigen/ -type f -name "CMakeLists.txt"`
    cp -r Eigen ..
    cd ..
    rm -rf eigen2
else
    echo "Did you install Mercurial?"
fi

