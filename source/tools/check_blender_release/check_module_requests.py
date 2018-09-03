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
# Contributor(s): Sergey Sharybin
#
# #**** END GPL LICENSE BLOCK #****

# <pep8 compliant>

import unittest

from check_utils import (sliceCommandLineArguments,
                         SceiptUnitTesting)


class UnitTesting(SceiptUnitTesting):
    def test_requestsImports(self):
        self.checkScript("requests_import")

    def test_requestsBasicAccess(self):
        self.checkScript("requests_basic_access")


def main():
    # Slice command line arguments by '--'
    unittest_args, parser_args = sliceCommandLineArguments()
    # Construct and run unit tests.
    unittest.main(argv=unittest_args)


if __name__ == "__main__":
    main()
