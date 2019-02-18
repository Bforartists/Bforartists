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

from svg_util import parse_array_of_floats
import unittest


class ParseArrayOfFloatsTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(parse_array_of_floats(""), [])
        self.assertEqual(parse_array_of_floats("    "), [])

    def test_single_value(self):
        self.assertEqual(parse_array_of_floats("123"), [123])
        self.assertEqual(parse_array_of_floats(" \t  123    \t"), [123])

    def test_single_value_exponent(self):
        self.assertEqual(parse_array_of_floats("12e+3"), [12000])
        self.assertEqual(parse_array_of_floats("12e-3"), [0.012])

    def test_space_separated_values(self):
        self.assertEqual(parse_array_of_floats("123 45 6 89"),
                                               [123, 45, 6, 89])
        self.assertEqual(parse_array_of_floats("    123 45   6 89 "),
                                               [123, 45, 6, 89])

    def test_comma_separated_values(self):
        self.assertEqual(parse_array_of_floats("123,45,6,89"),
                                               [123, 45, 6, 89])
        self.assertEqual(parse_array_of_floats("    123,45,6,89 "),
                                               [123, 45, 6, 89])

    def test_mixed_separated_values(self):
        self.assertEqual(parse_array_of_floats("123,45 6,89"),
                                               [123, 45, 6, 89])
        self.assertEqual(parse_array_of_floats("    123   45,6,89 "),
                                               [123, 45, 6, 89])

    def test_omitted_value_with_comma(self):
        self.assertEqual(parse_array_of_floats("1,,3"), [1, 0, 3])
        self.assertEqual(parse_array_of_floats(",,3"), [0, 0, 3])

    def test_sign_as_separator(self):
        self.assertEqual(parse_array_of_floats("1-3"), [1, -3])
        self.assertEqual(parse_array_of_floats("1+3"), [1, 3])

    def test_all_commas(self):
        self.assertEqual(parse_array_of_floats(",,,"), [0, 0, 0, 0])

    def test_value_with_decimal_separator(self):
        self.assertEqual(parse_array_of_floats("3.5"), [3.5])

    def test_comma_separated_values_with_decimal_separator(self):
        self.assertEqual(parse_array_of_floats("2.75,8.5"), [2.75, 8.5])


if __name__ == '__main__':
    unittest.main(verbosity=2)
