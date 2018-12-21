#!/usr/bin/env python3

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

"""
Sort commits by date (oldest first)
(useful for collecting commits to cherry pick)

Example:

    git_sort_commits.py < commits.txt
"""

import sys
import os

MODULE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "utils"))
SOURCE_DIR = os.path.normpath(os.path.join(MODULE_DIR, "..", "..", "..", ".git"))

sys.path.append(MODULE_DIR)

import git_log


def main():

    import re
    re_sha1_prefix = re.compile("^r[A-Z]+")

    def strip_sha1(sha1):
        # strip rB, rBA ... etc
        sha1 = re.sub(re_sha1_prefix, "", sha1)
        return sha1

    commits = [git_log.GitCommit(strip_sha1(l), SOURCE_DIR)
               for l in sys.stdin.read().split()]

    commits.sort(key=lambda c: c.date)

    for c in commits:
        print(c.sha1)


if __name__ == "__main__":
    main()
