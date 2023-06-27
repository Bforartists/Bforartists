#!/usr/bin/env python
# SPDX-FileCopyrightText: 2010 `Maximilian Hoegner <hp.maxi@hoegners.de>`
#
# SPDX-License-Identifier: GPL-3.0-or-later

# geo.py is a python module with no dependencies on extra packages,
# providing some convenience functions for working with geographic
# coordinates

### Part one - Functions for dealing with points on a sphere ###

### Part two - A tolerant parser for position strings ###
import re


class Parser:
    """ A parser class using regular expressions. """

    def __init__(self):
        self.patterns = {}
        self.raw_patterns = {}
        self.virtual = {}

    def add(self, name, pattern, virtual=False):
        """ Adds a new named pattern (regular expression) that can reference previously added patterns by %(pattern_name)s.
        Virtual patterns can be used to make expressions more compact but don't show up in the parse tree. """
        self.raw_patterns[name] = "(?:" + pattern + ")"
        self.virtual[name] = virtual

        try:
            self.patterns[name] = ("(?:" + pattern + ")") % self.patterns
        except KeyError as e:
            raise (Exception, "Unknown pattern name: %s" % str(e))

    def parse(self, pattern_name, text):
        """ Parses 'text' with pattern 'pattern_name' and returns parse tree """

        # build pattern with subgroups
        sub_dict = {}
        subpattern_names = []
        for s in re.finditer(r"%\(.*?\)s", self.raw_patterns[pattern_name]):
            subpattern_name = s.group()[2:-2]
            if not self.virtual[subpattern_name]:
                sub_dict[subpattern_name] = "(" + self.patterns[
                    subpattern_name] + ")"
                subpattern_names.append(subpattern_name)
            else:
                sub_dict[subpattern_name] = self.patterns[subpattern_name]

        pattern = "^" + (self.raw_patterns[pattern_name] % sub_dict) + "$"

        # do matching
        m = re.match(pattern, text)

        if m is None:
            return None

        # build tree recursively by parsing subgroups
        tree = {"TEXT": text}

        for i in range(len(subpattern_names)):
            text_part = m.group(i + 1)
            if text_part is not None:
                subpattern = subpattern_names[i]
                tree[subpattern] = self.parse(subpattern, text_part)

        return tree


position_parser = Parser()
position_parser.add("direction_ns", r"[NSns]")
position_parser.add("direction_ew", r"[EOWeow]")
position_parser.add("decimal_separator", r"[\.,]", True)
position_parser.add("sign", r"[+-]")

position_parser.add("nmea_style_degrees", r"[0-9]{2,}")
position_parser.add("nmea_style_minutes",
                    r"[0-9]{2}(?:%(decimal_separator)s[0-9]*)?")
position_parser.add(
    "nmea_style", r"%(sign)s?\s*%(nmea_style_degrees)s%(nmea_style_minutes)s")

position_parser.add(
    "number",
    r"[0-9]+(?:%(decimal_separator)s[0-9]*)?|%(decimal_separator)s[0-9]+")

position_parser.add("plain_degrees", r"(?:%(sign)s\s*)?%(number)s")

position_parser.add("degree_symbol", r"°", True)
position_parser.add("minutes_symbol", r"'|′|`|´", True)
position_parser.add("seconds_symbol",
                    r"%(minutes_symbol)s%(minutes_symbol)s|″|\"",
                    True)
position_parser.add("degrees", r"%(number)s\s*%(degree_symbol)s")
position_parser.add("minutes", r"%(number)s\s*%(minutes_symbol)s")
position_parser.add("seconds", r"%(number)s\s*%(seconds_symbol)s")
position_parser.add(
    "degree_coordinates",
    r"(?:%(sign)s\s*)?%(degrees)s(?:[+\s]*%(minutes)s)?(?:[+\s]*%(seconds)s)?|(?:%(sign)s\s*)%(minutes)s(?:[+\s]*%(seconds)s)?|(?:%(sign)s\s*)%(seconds)s"
)

position_parser.add(
    "coordinates_ns",
    r"%(nmea_style)s|%(plain_degrees)s|%(degree_coordinates)s")
position_parser.add(
    "coordinates_ew",
    r"%(nmea_style)s|%(plain_degrees)s|%(degree_coordinates)s")

position_parser.add(
    "position", (
        r"\s*%(direction_ns)s\s*%(coordinates_ns)s[,;\s]*%(direction_ew)s\s*%(coordinates_ew)s\s*|"
        r"\s*%(direction_ew)s\s*%(coordinates_ew)s[,;\s]*%(direction_ns)s\s*%(coordinates_ns)s\s*|"
        r"\s*%(coordinates_ns)s\s*%(direction_ns)s[,;\s]*%(coordinates_ew)s\s*%(direction_ew)s\s*|"
        r"\s*%(coordinates_ew)s\s*%(direction_ew)s[,;\s]*%(coordinates_ns)s\s*%(direction_ns)s\s*|"
        r"\s*%(coordinates_ns)s[,;\s]+%(coordinates_ew)s\s*"
    ))


def get_number(b):
    """ Takes appropriate branch of parse tree and returns float. """
    s = b["TEXT"].replace(",", ".")
    return float(s)


def get_coordinate(b):
    """ Takes appropriate branch of the parse tree and returns degrees as a float. """

    r = 0.

    if b.get("nmea_style"):
        if b["nmea_style"].get("nmea_style_degrees"):
            r += get_number(b["nmea_style"]["nmea_style_degrees"])
        if b["nmea_style"].get("nmea_style_minutes"):
            r += get_number(b["nmea_style"]["nmea_style_minutes"]) / 60.
        if b["nmea_style"].get(
                "sign") and b["nmea_style"]["sign"]["TEXT"] == "-":
            r *= -1.
    elif b.get("plain_degrees"):
        r += get_number(b["plain_degrees"]["number"])
        if b["plain_degrees"].get(
                "sign") and b["plain_degrees"]["sign"]["TEXT"] == "-":
            r *= -1.
    elif b.get("degree_coordinates"):
        if b["degree_coordinates"].get("degrees"):
            r += get_number(b["degree_coordinates"]["degrees"]["number"])
        if b["degree_coordinates"].get("minutes"):
            r += get_number(b["degree_coordinates"]["minutes"]["number"]) / 60.
        if b["degree_coordinates"].get("seconds"):
            r += get_number(
                b["degree_coordinates"]["seconds"]["number"]) / 3600.
        if b["degree_coordinates"].get(
                "sign") and b["degree_coordinates"]["sign"]["TEXT"] == "-":
            r *= -1.

    return r


def parse_position(s):
    """ Takes a (utf8-encoded) string describing a position and returns a tuple of floats for latitude and longitude in degrees.
    Tries to be as tolerant as possible with input. Returns None if parsing doesn't succeed. """

    parse_tree = position_parser.parse("position", s)
    if parse_tree is None:
        return None

    lat_sign = +1.
    if parse_tree.get(
            "direction_ns") and parse_tree["direction_ns"]["TEXT"] in ("S",
                                                                       "s"):
        lat_sign = -1.

    lon_sign = +1.
    if parse_tree.get(
            "direction_ew") and parse_tree["direction_ew"]["TEXT"] in ("W",
                                                                       "w"):
        lon_sign = -1.

    lat = lat_sign * get_coordinate(parse_tree["coordinates_ns"])
    lon = lon_sign * get_coordinate(parse_tree["coordinates_ew"])

    return lat, lon
