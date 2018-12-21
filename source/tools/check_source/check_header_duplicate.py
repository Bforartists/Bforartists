#!/usr/bin/env python3

# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Contributor(s): Campbell Barton
#
# ***** END GPL LICENSE BLOCK *****

# <pep8 compliant>

"""
Run this script to check if headers are included multiple times.

    python3 check_header_duplicate.py ../../

Now build the code to find duplicate errors, resolve them manually.

Then restore the headers to their original state:

    python3 check_header_duplicate.py --restore ../../
"""

# Use GCC's __INCLUDE_LEVEL__ to find direct duplicate includes

UUID = 0


def source_filepath_guard(filepath):
    global UUID

    footer = """
#if __INCLUDE_LEVEL__ == 1
#  ifdef _DOUBLEHEADERGUARD_%d
#    error "duplicate header!"
#  endif
#endif

#if __INCLUDE_LEVEL__ == 1
#  define _DOUBLEHEADERGUARD_%d
#endif
""" % (UUID, UUID)
    UUID += 1

    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(footer)


def source_filepath_restore(filepath):
    import os
    os.system("git co %s" % filepath)


def scan_source_recursive(dirpath, is_restore):
    import os
    from os.path import join, splitext

    # ensure git working dir is ok
    os.chdir(dirpath)

    def source_list(path, filename_check=None):
        for dirpath, dirnames, filenames in os.walk(path):
            # skip '.git'
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]

            for filename in filenames:
                filepath = join(dirpath, filename)
                if filename_check is None or filename_check(filepath):
                    yield filepath

    def is_source(filename):
        ext = splitext(filename)[1]
        return (ext in {".hpp", ".hxx", ".h", ".hh"})

    def is_ignore(filename):
        pass

    for filepath in sorted(source_list(dirpath, is_source)):
        print("file:", filepath)
        if is_ignore(filepath):
            continue

        if is_restore:
            source_filepath_restore(filepath)
        else:
            source_filepath_guard(filepath)


def main():
    import sys
    is_restore = ("--restore" in sys.argv[1:])
    scan_source_recursive(sys.argv[-1], is_restore)


if __name__ == "__main__":
    main()
