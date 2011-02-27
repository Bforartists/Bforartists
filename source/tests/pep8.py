# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import os

# depends on pep8, pyflakes, pylint
# for ubuntu
#
#   sudo apt-get install pylint pyflakes
#
#   sudo apt-get install python-setuptools python-pip
#   sudo pip install pep8
#
# in debian install pylint pyflakes pep8 with apt-get/aptitude/etc
#
# on *nix run
#   python release/test/pep8.py > pep8_error.txt 2>&1

# how many lines to read into the file, pep8 comment
# should be directly after the licence header, ~20 in most cases
PEP8_SEEK_COMMENT = 40
SKIP_PREFIX = "./tools", "./config", "./scons", "./extern"


def file_list_py(path):
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(".py"):
                yield os.path.join(dirpath, filename)


def is_pep8(path):
    print(path)
    if open(path, 'rb').read(3) == b'\xef\xbb\xbf':
        print("\nfile contains BOM, remove first 3 bytes: %r\n" % path)

    # templates dont have a header but should be pep8
    for d in ("presets", "templates", "examples"):
        if ("%s%s%s" % (os.sep, d, os.sep)) in path:
            return 1

    f = open(path, 'r', encoding="utf8")
    for i in range(PEP8_SEEK_COMMENT):
        line = f.readline()
        if line.startswith("# <pep8"):
            if line.startswith("# <pep8 compliant>"):
                return 1
            elif line.startswith("# <pep8-80 compliant>"):
                return 2
    f.close()
    return 0


def main():
    files = []
    files_skip = []
    for f in file_list_py("."):
        if [None for prefix in SKIP_PREFIX if f.startswith(prefix)]:
            continue

        pep8_type = is_pep8(f)

        if pep8_type:
            # so we can batch them for each tool.
            files.append((os.path.abspath(f), pep8_type))
        else:
            files_skip.append(f)

    print("\nSkipping...")
    for f in files_skip:
        print("    %s" % f)

    # pyflakes
    print("\n\n\n# running pep8...")
    for f, pep8_type in files:
        if pep8_type == 1:
            # E501:80 line length
            os.system("pep8 --repeat --ignore=E501 '%s'" % (f))
        else:
            os.system("pep8 --repeat '%s'" % (f))

    print("\n\n\n# running pyflakes...")
    for f, pep8_type in files:
        os.system("pyflakes '%s'" % f)

    print("\n\n\n# running pylint...")
    for f, pep8_type in files:
        # let pep8 complain about line length
        os.system("pylint --reports=n --max-line-length=1000 '%s'" % f)

if __name__ == "__main__":
    main()
