#!/usr/bin/python

#update the pot file according the POTFILES.in

import os

GETTEXT_XGETTEXT_EXECUTABLE="xgettext"
SOURCE_DIR=".."
DOMAIN="blender"

cmd = "%s --files-from=%s/po/POTFILES.in --keyword=_ --keyword=gettext --directory=%s --output=%s/po/%s.pot" % (
    GETTEXT_XGETTEXT_EXECUTABLE, SOURCE_DIR, SOURCE_DIR, SOURCE_DIR, DOMAIN)

os.system( cmd )
