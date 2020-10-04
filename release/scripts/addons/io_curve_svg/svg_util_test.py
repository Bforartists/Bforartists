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


# XXX Not really nice, but that hack is needed to allow execution of that test
#     from both automated CTest and by directly running the file manually.
if __name__ == '__main__':
    from svg_util import (parse_array_of_floats, read_float, parse_coord,)
else:
    from .svg_util import (parse_array_of_floats, read_float, parse_coord,)
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

    def test_missing_decimal(self):
        self.assertEqual(parse_array_of_floats(".92"), [0.92])
        self.assertEqual(parse_array_of_floats(".92e+1"), [9.2])

        self.assertEqual(parse_array_of_floats("-.92"), [-0.92])
        self.assertEqual(parse_array_of_floats("-.92e+1"), [-9.2])


class ReadFloatTest(unittest.TestCase):
    def test_empty(self):
        value, endptr = read_float("", 0)
        self.assertEqual(value, "0")
        self.assertEqual(endptr, 0)

    def test_empty_spaces(self):
        value, endptr = read_float("    ", 0)
        self.assertEqual(value, "0")
        self.assertEqual(endptr, 4)

    def test_single_value(self):
        value, endptr = read_float("1.2", 0)
        self.assertEqual(value, "1.2")
        self.assertEqual(endptr, 3)

    def test_scientific_value(self):
        value, endptr = read_float("1.2e+3", 0)
        self.assertEqual(value, "1.2e+3")
        self.assertEqual(endptr, 6)

    def test_scientific_value_no_sign(self):
        value, endptr = read_float("1.2e3", 0)
        self.assertEqual(value, "1.2e3")
        self.assertEqual(endptr, 5)

    def test_middle(self):
        value, endptr = read_float("1.2  3.4  5.6", 3)
        self.assertEqual(value, "3.4")
        self.assertEqual(endptr, 8)

    def test_comma(self):
        value, endptr = read_float("1.2  ,,3.4  5.6", 3)
        self.assertEqual(value, "3.4")
        self.assertEqual(endptr, 10)

    def test_not_a_number(self):
        # TODO(sergey): Make this catch more concrete.
        with self.assertRaises(Exception):
            read_float("1.2eV", 3)

    def test_missing_fractional(self):
        value, endptr = read_float("1.", 0)
        self.assertEqual(value, "1.")
        self.assertEqual(endptr, 2)

        value, endptr = read_float("2. 3", 0)
        self.assertEqual(value, "2.")
        self.assertEqual(endptr, 2)

    def test_missing_decimal(self):
        value, endptr = read_float(".92", 0)
        self.assertEqual(value, ".92")
        self.assertEqual(endptr, 3)

        value, endptr = read_float("-.92", 0)
        self.assertEqual(value, "-.92")
        self.assertEqual(endptr, 4)

        value, endptr = read_float(".92e+3", 0)
        self.assertEqual(value, ".92e+3")
        self.assertEqual(endptr, 6)

        value, endptr = read_float("-.92e+3", 0)
        self.assertEqual(value, "-.92e+3")
        self.assertEqual(endptr, 7)

        # TODO(sergey): Make these catch more concrete.
        with self.assertRaises(Exception):
            read_float(".", 0)
        with self.assertRaises(Exception):
            read_float(".e+1", 0)


class ParseCoordTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(parse_coord("", 200), 0)

    def test_empty_spaces(self):
        self.assertEqual(parse_coord("    ", 200), 0)

    def test_no_units(self):
        self.assertEqual(parse_coord("1.2", 200), 1.2)

    def test_unit_cm(self):
        self.assertAlmostEqual(parse_coord("1.2cm", 200), 42.51968503937008)

    def test_unit_ex(self):
        self.assertAlmostEqual(parse_coord("1.2ex", 200), 1.2)

    def test_unit_percentage(self):
        self.assertEqual(parse_coord("1.2%", 200), 2.4)


if __name__ == '__main__':
    unittest.main(verbosity=2)
