# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import bpy
import bmesh
from math import pi, cos, sin, sqrt, ceil
from mathutils import Vector, Matrix
from copy import copy

# -----------------------------------------------------------------------------
#                                                  Atom, stick and element data


# This is a list that contains some data of all possible elements. The structure
# is as follows:
#
# 1, "Hydrogen", "H", [0.0,0.0,1.0], 0.32, 0.32, 0.32 , -1 , 1.54   means
#
# No., name, short name, color, radius (used), radius (covalent), radius (atomic),
#
# charge state 1, radius (ionic) 1, charge state 2, radius (ionic) 2, ... all
# charge states for any atom are listed, if existing.
# The list is fixed and cannot be changed ... (see below)

ELEMENTS_DEFAULT = (
( 1,      "Hydrogen",        "H",  (  1.0,   1.0,   1.0, 1.0), 0.32, 0.32, 0.79 , -1 , 1.54 ),
( 2,        "Helium",       "He",  ( 0.85,   1.0,   1.0, 1.0), 0.93, 0.93, 0.49 ),
( 3,       "Lithium",       "Li",  (  0.8,  0.50,   1.0, 1.0), 1.23, 1.23, 2.05 ,  1 , 0.68 ),
( 4,     "Beryllium",       "Be",  ( 0.76,   1.0,   0.0, 1.0), 0.90, 0.90, 1.40 ,  1 , 0.44 ,  2 , 0.35 ),
( 5,         "Boron",        "B",  (  1.0,  0.70,  0.70, 1.0), 0.82, 0.82, 1.17 ,  1 , 0.35 ,  3 , 0.23 ),
( 6,        "Carbon",        "C",  ( 0.56,  0.56,  0.56, 1.0), 0.77, 0.77, 0.91 , -4 , 2.60 ,  4 , 0.16 ),
( 7,      "Nitrogen",        "N",  ( 0.18,  0.31,  0.97, 1.0), 0.75, 0.75, 0.75 , -3 , 1.71 ,  1 , 0.25 ,  3 , 0.16 ,  5 , 0.13 ),
( 8,        "Oxygen",        "O",  (  1.0,  0.05,  0.05, 1.0), 0.73, 0.73, 0.65 , -2 , 1.32 , -1 , 1.76 ,  1 , 0.22 ,  6 , 0.09 ),
( 9,      "Fluorine",        "F",  ( 0.56,  0.87,  0.31, 1.0), 0.72, 0.72, 0.57 , -1 , 1.33 ,  7 , 0.08 ),
(10,          "Neon",       "Ne",  ( 0.70,  0.89,  0.96, 1.0), 0.71, 0.71, 0.51 ,  1 , 1.12 ),
(11,        "Sodium",       "Na",  ( 0.67,  0.36,  0.94, 1.0), 1.54, 1.54, 2.23 ,  1 , 0.97 ),
(12,     "Magnesium",       "Mg",  ( 0.54,   1.0,   0.0, 1.0), 1.36, 1.36, 1.72 ,  1 , 0.82 ,  2 , 0.66 ),
(13,     "Aluminium",       "Al",  ( 0.74,  0.65,  0.65, 1.0), 1.18, 1.18, 1.82 ,  3 , 0.51 ),
(14,       "Silicon",       "Si",  ( 0.94,  0.78,  0.62, 1.0), 1.11, 1.11, 1.46 , -4 , 2.71 , -1 , 3.84 ,  1 , 0.65 ,  4 , 0.42 ),
(15,    "Phosphorus",        "P",  (  1.0,  0.50,   0.0, 1.0), 1.06, 1.06, 1.23 , -3 , 2.12 ,  3 , 0.44 ,  5 , 0.35 ),
(16,        "Sulfur",        "S",  (  1.0,   1.0,  0.18, 1.0), 1.02, 1.02, 1.09 , -2 , 1.84 ,  2 , 2.19 ,  4 , 0.37 ,  6 , 0.30 ),
(17,      "Chlorine",       "Cl",  ( 0.12,  0.94,  0.12, 1.0), 0.99, 0.99, 0.97 , -1 , 1.81 ,  5 , 0.34 ,  7 , 0.27 ),
(18,         "Argon",       "Ar",  ( 0.50,  0.81,  0.89, 1.0), 0.98, 0.98, 0.88 ,  1 , 1.54 ),
(19,     "Potassium",        "K",  ( 0.56,  0.25,  0.83, 1.0), 2.03, 2.03, 2.77 ,  1 , 0.81 ),
(20,       "Calcium",       "Ca",  ( 0.23,   1.0,   0.0, 1.0), 1.74, 1.74, 2.23 ,  1 , 1.18 ,  2 , 0.99 ),
(21,      "Scandium",       "Sc",  ( 0.90,  0.90,  0.90, 1.0), 1.44, 1.44, 2.09 ,  3 , 0.73 ),
(22,      "Titanium",       "Ti",  ( 0.74,  0.76,  0.78, 1.0), 1.32, 1.32, 2.00 ,  1 , 0.96 ,  2 , 0.94 ,  3 , 0.76 ,  4 , 0.68 ),
(23,      "Vanadium",        "V",  ( 0.65,  0.65,  0.67, 1.0), 1.22, 1.22, 1.92 ,  2 , 0.88 ,  3 , 0.74 ,  4 , 0.63 ,  5 , 0.59 ),
(24,      "Chromium",       "Cr",  ( 0.54,   0.6,  0.78, 1.0), 1.18, 1.18, 1.85 ,  1 , 0.81 ,  2 , 0.89 ,  3 , 0.63 ,  6 , 0.52 ),
(25,     "Manganese",       "Mn",  ( 0.61,  0.47,  0.78, 1.0), 1.17, 1.17, 1.79 ,  2 , 0.80 ,  3 , 0.66 ,  4 , 0.60 ,  7 , 0.46 ),
(26,          "Iron",       "Fe",  ( 0.87,   0.4,   0.2, 1.0), 1.17, 1.17, 1.72 ,  2 , 0.74 ,  3 , 0.64 ),
(27,        "Cobalt",       "Co",  ( 0.94,  0.56,  0.62, 1.0), 1.16, 1.16, 1.67 ,  2 , 0.72 ,  3 , 0.63 ),
(28,        "Nickel",       "Ni",  ( 0.31,  0.81,  0.31, 1.0), 1.15, 1.15, 1.62 ,  2 , 0.69 ),
(29,        "Copper",       "Cu",  ( 0.78,  0.50,   0.2, 1.0), 1.17, 1.17, 1.57 ,  1 , 0.96 ,  2 , 0.72 ),
(30,          "Zinc",       "Zn",  ( 0.49,  0.50,  0.69, 1.0), 1.25, 1.25, 1.53 ,  1 , 0.88 ,  2 , 0.74 ),
(31,       "Gallium",       "Ga",  ( 0.76,  0.56,  0.56, 1.0), 1.26, 1.26, 1.81 ,  1 , 0.81 ,  3 , 0.62 ),
(32,     "Germanium",       "Ge",  (  0.4,  0.56,  0.56, 1.0), 1.22, 1.22, 1.52 , -4 , 2.72 ,  2 , 0.73 ,  4 , 0.53 ),
(33,       "Arsenic",       "As",  ( 0.74,  0.50,  0.89, 1.0), 1.20, 1.20, 1.33 , -3 , 2.22 ,  3 , 0.58 ,  5 , 0.46 ),
(34,      "Selenium",       "Se",  (  1.0,  0.63,   0.0, 1.0), 1.16, 1.16, 1.22 , -2 , 1.91 , -1 , 2.32 ,  1 , 0.66 ,  4 , 0.50 ,  6 , 0.42 ),
(35,       "Bromine",       "Br",  ( 0.65,  0.16,  0.16, 1.0), 1.14, 1.14, 1.12 , -1 , 1.96 ,  5 , 0.47 ,  7 , 0.39 ),
(36,       "Krypton",       "Kr",  ( 0.36,  0.72,  0.81, 1.0), 1.31, 1.31, 1.24 ),
(37,      "Rubidium",       "Rb",  ( 0.43,  0.18,  0.69, 1.0), 2.16, 2.16, 2.98 ,  1 , 1.47 ),
(38,     "Strontium",       "Sr",  (  0.0,   1.0,   0.0, 1.0), 1.91, 1.91, 2.45 ,  2 , 1.12 ),
(39,       "Yttrium",        "Y",  ( 0.58,   1.0,   1.0, 1.0), 1.62, 1.62, 2.27 ,  3 , 0.89 ),
(40,     "Zirconium",       "Zr",  ( 0.58,  0.87,  0.87, 1.0), 1.45, 1.45, 2.16 ,  1 , 1.09 ,  4 , 0.79 ),
(41,       "Niobium",       "Nb",  ( 0.45,  0.76,  0.78, 1.0), 1.34, 1.34, 2.08 ,  1 , 1.00 ,  4 , 0.74 ,  5 , 0.69 ),
(42,    "Molybdenum",       "Mo",  ( 0.32,  0.70,  0.70, 1.0), 1.30, 1.30, 2.01 ,  1 , 0.93 ,  4 , 0.70 ,  6 , 0.62 ),
(43,    "Technetium",       "Tc",  ( 0.23,  0.61,  0.61, 1.0), 1.27, 1.27, 1.95 ,  7 , 0.97 ),
(44,     "Ruthenium",       "Ru",  ( 0.14,  0.56,  0.56, 1.0), 1.25, 1.25, 1.89 ,  4 , 0.67 ),
(45,       "Rhodium",       "Rh",  ( 0.03,  0.49,  0.54, 1.0), 1.25, 1.25, 1.83 ,  3 , 0.68 ),
(46,     "Palladium",       "Pd",  (  0.0,  0.41,  0.52, 1.0), 1.28, 1.28, 1.79 ,  2 , 0.80 ,  4 , 0.65 ),
(47,        "Silver",       "Ag",  ( 0.75,  0.75,  0.75, 1.0), 1.34, 1.34, 1.75 ,  1 , 1.26 ,  2 , 0.89 ),
(48,       "Cadmium",       "Cd",  (  1.0,  0.85,  0.56, 1.0), 1.48, 1.48, 1.71 ,  1 , 1.14 ,  2 , 0.97 ),
(49,        "Indium",       "In",  ( 0.65,  0.45,  0.45, 1.0), 1.44, 1.44, 2.00 ,  3 , 0.81 ),
(50,           "Tin",       "Sn",  (  0.4,  0.50,  0.50, 1.0), 1.41, 1.41, 1.72 , -4 , 2.94 , -1 , 3.70 ,  2 , 0.93 ,  4 , 0.71 ),
(51,      "Antimony",       "Sb",  ( 0.61,  0.38,  0.70, 1.0), 1.40, 1.40, 1.53 , -3 , 2.45 ,  3 , 0.76 ,  5 , 0.62 ),
(52,     "Tellurium",       "Te",  ( 0.83,  0.47,   0.0, 1.0), 1.36, 1.36, 1.42 , -2 , 2.11 , -1 , 2.50 ,  1 , 0.82 ,  4 , 0.70 ,  6 , 0.56 ),
(53,        "Iodine",        "I",  ( 0.58,   0.0,  0.58, 1.0), 1.33, 1.33, 1.32 , -1 , 2.20 ,  5 , 0.62 ,  7 , 0.50 ),
(54,         "Xenon",       "Xe",  ( 0.25,  0.61,  0.69, 1.0), 1.31, 1.31, 1.24 ),
(55,       "Caesium",       "Cs",  ( 0.34,  0.09,  0.56, 1.0), 2.35, 2.35, 3.35 ,  1 , 1.67 ),
(56,        "Barium",       "Ba",  (  0.0,  0.78,   0.0, 1.0), 1.98, 1.98, 2.78 ,  1 , 1.53 ,  2 , 1.34 ),
(57,     "Lanthanum",       "La",  ( 0.43,  0.83,   1.0, 1.0), 1.69, 1.69, 2.74 ,  1 , 1.39 ,  3 , 1.06 ),
(58,        "Cerium",       "Ce",  (  1.0,   1.0,  0.78, 1.0), 1.65, 1.65, 2.70 ,  1 , 1.27 ,  3 , 1.03 ,  4 , 0.92 ),
(59,  "Praseodymium",       "Pr",  ( 0.85,   1.0,  0.78, 1.0), 1.65, 1.65, 2.67 ,  3 , 1.01 ,  4 , 0.90 ),
(60,     "Neodymium",       "Nd",  ( 0.78,   1.0,  0.78, 1.0), 1.64, 1.64, 2.64 ,  3 , 0.99 ),
(61,    "Promethium",       "Pm",  ( 0.63,   1.0,  0.78, 1.0), 1.63, 1.63, 2.62 ,  3 , 0.97 ),
(62,      "Samarium",       "Sm",  ( 0.56,   1.0,  0.78, 1.0), 1.62, 1.62, 2.59 ,  3 , 0.96 ),
(63,      "Europium",       "Eu",  ( 0.38,   1.0,  0.78, 1.0), 1.85, 1.85, 2.56 ,  2 , 1.09 ,  3 , 0.95 ),
(64,    "Gadolinium",       "Gd",  ( 0.27,   1.0,  0.78, 1.0), 1.61, 1.61, 2.54 ,  3 , 0.93 ),
(65,       "Terbium",       "Tb",  ( 0.18,   1.0,  0.78, 1.0), 1.59, 1.59, 2.51 ,  3 , 0.92 ,  4 , 0.84 ),
(66,    "Dysprosium",       "Dy",  ( 0.12,   1.0,  0.78, 1.0), 1.59, 1.59, 2.49 ,  3 , 0.90 ),
(67,       "Holmium",       "Ho",  (  0.0,   1.0,  0.61, 1.0), 1.58, 1.58, 2.47 ,  3 , 0.89 ),
(68,        "Erbium",       "Er",  (  0.0,  0.90,  0.45, 1.0), 1.57, 1.57, 2.45 ,  3 , 0.88 ),
(69,       "Thulium",       "Tm",  (  0.0,  0.83,  0.32, 1.0), 1.56, 1.56, 2.42 ,  3 , 0.87 ),
(70,     "Ytterbium",       "Yb",  (  0.0,  0.74,  0.21, 1.0), 1.74, 1.74, 2.40 ,  2 , 0.93 ,  3 , 0.85 ),
(71,      "Lutetium",       "Lu",  (  0.0,  0.67,  0.14, 1.0), 1.56, 1.56, 2.25 ,  3 , 0.85 ),
(72,       "Hafnium",       "Hf",  ( 0.30,  0.76,   1.0, 1.0), 1.44, 1.44, 2.16 ,  4 , 0.78 ),
(73,      "Tantalum",       "Ta",  ( 0.30,  0.65,   1.0, 1.0), 1.34, 1.34, 2.09 ,  5 , 0.68 ),
(74,      "Tungsten",        "W",  ( 0.12,  0.58,  0.83, 1.0), 1.30, 1.30, 2.02 ,  4 , 0.70 ,  6 , 0.62 ),
(75,       "Rhenium",       "Re",  ( 0.14,  0.49,  0.67, 1.0), 1.28, 1.28, 1.97 ,  4 , 0.72 ,  7 , 0.56 ),
(76,        "Osmium",       "Os",  ( 0.14,   0.4,  0.58, 1.0), 1.26, 1.26, 1.92 ,  4 , 0.88 ,  6 , 0.69 ),
(77,       "Iridium",       "Ir",  ( 0.09,  0.32,  0.52, 1.0), 1.27, 1.27, 1.87 ,  4 , 0.68 ),
(78,      "Platinum",       "Pt",  ( 0.81,  0.81,  0.87, 1.0), 1.30, 1.30, 1.83 ,  2 , 0.80 ,  4 , 0.65 ),
(79,          "Gold",       "Au",  (  1.0,  0.81,  0.13, 1.0), 1.34, 1.34, 1.79 ,  1 , 1.37 ,  3 , 0.85 ),
(80,       "Mercury",       "Hg",  ( 0.72,  0.72,  0.81, 1.0), 1.49, 1.49, 1.76 ,  1 , 1.27 ,  2 , 1.10 ),
(81,      "Thallium",       "Tl",  ( 0.65,  0.32,  0.30, 1.0), 1.48, 1.48, 2.08 ,  1 , 1.47 ,  3 , 0.95 ),
(82,          "Lead",       "Pb",  ( 0.34,  0.34,  0.38, 1.0), 1.47, 1.47, 1.81 ,  2 , 1.20 ,  4 , 0.84 ),
(83,       "Bismuth",       "Bi",  ( 0.61,  0.30,  0.70, 1.0), 1.46, 1.46, 1.63 ,  1 , 0.98 ,  3 , 0.96 ,  5 , 0.74 ),
(84,      "Polonium",       "Po",  ( 0.67,  0.36,   0.0, 1.0), 1.46, 1.46, 1.53 ,  6 , 0.67 ),
(85,      "Astatine",       "At",  ( 0.45,  0.30,  0.27, 1.0), 1.45, 1.45, 1.43 , -3 , 2.22 ,  3 , 0.85 ,  5 , 0.46 ),
(86,         "Radon",       "Rn",  ( 0.25,  0.50,  0.58, 1.0), 1.00, 1.00, 1.34 ),
(87,      "Francium",       "Fr",  ( 0.25,   0.0,   0.4, 1.0), 1.00, 1.00, 1.00 ,  1 , 1.80 ),
(88,        "Radium",       "Ra",  (  0.0,  0.49,   0.0, 1.0), 1.00, 1.00, 1.00 ,  2 , 1.43 ),
(89,      "Actinium",       "Ac",  ( 0.43,  0.67,  0.98, 1.0), 1.00, 1.00, 1.00 ,  3 , 1.18 ),
(90,       "Thorium",       "Th",  (  0.0,  0.72,   1.0, 1.0), 1.65, 1.65, 1.00 ,  4 , 1.02 ),
(91,  "Protactinium",       "Pa",  (  0.0,  0.63,   1.0, 1.0), 1.00, 1.00, 1.00 ,  3 , 1.13 ,  4 , 0.98 ,  5 , 0.89 ),
(92,       "Uranium",        "U",  (  0.0,  0.56,   1.0, 1.0), 1.42, 1.42, 1.00 ,  4 , 0.97 ,  6 , 0.80 ),
(93,     "Neptunium",       "Np",  (  0.0,  0.50,   1.0, 1.0), 1.00, 1.00, 1.00 ,  3 , 1.10 ,  4 , 0.95 ,  7 , 0.71 ),
(94,     "Plutonium",       "Pu",  (  0.0,  0.41,   1.0, 1.0), 1.00, 1.00, 1.00 ,  3 , 1.08 ,  4 , 0.93 ),
(95,     "Americium",       "Am",  ( 0.32,  0.36,  0.94, 1.0), 1.00, 1.00, 1.00 ,  3 , 1.07 ,  4 , 0.92 ),
(96,        "Curium",       "Cm",  ( 0.47,  0.36,  0.89, 1.0), 1.00, 1.00, 1.00 ),
(97,     "Berkelium",       "Bk",  ( 0.54,  0.30,  0.89, 1.0), 1.00, 1.00, 1.00 ),
(98,   "Californium",       "Cf",  ( 0.63,  0.21,  0.83, 1.0), 1.00, 1.00, 1.00 ),
(99,   "Einsteinium",       "Es",  ( 0.70,  0.12,  0.83, 1.0), 1.00, 1.00, 1.00 ),
(100,       "Fermium",       "Fm", ( 0.70,  0.12,  0.72, 1.0), 1.00, 1.00, 1.00 ),
(101,   "Mendelevium",       "Md", ( 0.70,  0.05,  0.65, 1.0), 1.00, 1.00, 1.00 ),
(102,      "Nobelium",       "No", ( 0.74,  0.05,  0.52, 1.0), 1.00, 1.00, 1.00 ),
(103,    "Lawrencium",       "Lr", ( 0.78,   0.0,   0.4, 1.0), 1.00, 1.00, 1.00 ),
(104,       "Vacancy",      "Vac", (  0.5,   0.5,   0.5, 1.0), 1.00, 1.00, 1.00),
(105,       "Default",  "Default", (  1.0,   1.0,   1.0, 1.0), 1.00, 1.00, 1.00),
(106,         "Stick",    "Stick", (  0.5,   0.5,   0.5, 1.0), 1.00, 1.00, 1.00),
)

# This list here contains all data of the elements and will be used during
# runtime. It is a list of classes.
# During executing Atomic Blender, the list will be initialized with the fixed
# data from above via the class structure below (ElementProp). We
# have then one fixed list (above), which will never be changed, and a list of
# classes with same data. The latter can be modified via loading a separate
# custom data file.
ELEMENTS = []

# This is the class, which stores the properties for one element.
class ElementProp(object):
    __slots__ = ('number', 'name', 'short_name', 'color', 'radii', 'radii_ionic')
    def __init__(self, number, name, short_name, color, radii, radii_ionic):
        self.number = number
        self.name = name
        self.short_name = short_name
        self.color = color
        self.radii = radii
        self.radii_ionic = radii_ionic

# This is the class, which stores the properties of one atom.
class AtomProp(object):
    __slots__ = ('element', 'name', 'location', 'radius', 'color', 'material')
    def __init__(self, element, name, location, radius, color, material):
        self.element = element
        self.name = name
        self.location = location
        self.radius = radius
        self.color = color
        self.material = material

# This is the class, which stores the two atoms of one stick.
class StickProp(object):
    __slots__ = ('atom1', 'atom2', 'number', 'dist')
    def __init__(self, atom1, atom2, number, dist):
        self.atom1 = atom1
        self.atom2 = atom2
        self.number = number
        self.dist = dist

# -----------------------------------------------------------------------------
#                                                           Some basic routines


# The function, which reads all necessary properties of the elements.
def read_elements():

    del ELEMENTS[:]

    for item in ELEMENTS_DEFAULT:

        # All three radii into a list
        radii = [item[4],item[5],item[6]]
        # The handling of the ionic radii will be done later. So far, it is an
        # empty list.
        radii_ionic = []

        li = ElementProp(item[0],item[1],item[2],item[3],
                                     radii,radii_ionic)
        ELEMENTS.append(li)


# The function, which reads the x,y,z positions of all atoms in a PDB
# file.
#
# filepath_pdb: path to pdb file
# radiustype  : '0' default
#               '1' atomic radii
#               '2' van der Waals
def read_pdb_file(filepath_pdb, radiustype):

    # The list of all atoms as read from the PDB file.
    all_atoms  = []

    # Open the pdb file ...
    filepath_pdb_p = open(filepath_pdb, "r")

    #Go to the line, in which "ATOM" or "HETATM" appears.
    for line in filepath_pdb_p:
        split_list = line.split(' ')
        if "ATOM" in split_list[0]:
            break
        if "HETATM" in split_list[0]:
            break

    j = 0
    # This is in fact an endless 'while loop', ...
    while j > -1:

        # ... the loop is broken here (EOF) ...
        if line == "":
            break

        # If there is a "TER" we need to put empty entries into the lists
        # in order to not destroy the order of atom numbers and same numbers
        # used for sticks. "TER? What is that?" TER indicates the end of a
        # list of ATOM/HETATM records for a chain.
        if "TER" in line:
            short_name = "TER"
            name = "TER"
            radius = 0.0
            # 2019-03-14, New
            color = [0,0,0, 0]
            location = Vector((0,0,0))
            # Append the TER into the list. Material remains empty so far.
            all_atoms.append(AtomProp(short_name,
                                      name,
                                      location,
                                      radius,
                                      color,[]))

        # If 'ATOM or 'HETATM' appears in the line then do ...
        elif "ATOM" in line or "HETATM" in line:

            # What follows is due to deviations which appear from PDB to
            # PDB file. It is very special!
            #
            # PLEASE, DO NOT CHANGE! ............................... from here
            if line[12:13] == " " or line[12:13].isdigit() == True:
                short_name = line[13:14]
                if line[14:15].islower() == True:
                    short_name = short_name + line[14:15]
            elif line[12:13].isupper() == True:
                short_name = line[12:13]
                if line[13:14].isalpha() == True:
                    short_name = short_name + line[13:14]
            else:
                print("Atomic Blender: Strange error in PDB file.\n"
                      "Look for element names at positions 13-16 and 78-79.\n")
                return -1

            if len(line) >= 78:

                if line[76:77] == " ":
                    short_name2 = line[76:77]
                else:
                    short_name2 = line[76:78]

                if short_name2.isalpha() == True:
                    FOUND = False
                    for element in ELEMENTS:
                        if str.upper(short_name2) == str.upper(element.short_name):
                            FOUND = True
                            break
                    if FOUND == False:
                        short_name = short_name2

            # ....................................................... to here.

            # Go through all elements and find the element of the current atom.
            FLAG_FOUND = False
            for element in ELEMENTS:
                if str.upper(short_name) == str.upper(element.short_name):
                    # Give the atom its proper names, color and radius:
                    short_name = str.upper(element.short_name)
                    name = element.name
                    # int(radiustype) => type of radius:
                    # pre-defined (0), atomic (1) or van der Waals (2)
                    radius = float(element.radii[int(radiustype)])
                    color = element.color
                    FLAG_FOUND = True
                    break

            # Is it a vacancy or an 'unknown atom' ?
            if FLAG_FOUND == False:
                # Give this atom also a name. If it is an 'X' then it is a
                # vacancy. Otherwise ...
                if "X" in short_name:
                    short_name = "VAC"
                    name = "Vacancy"
                    radius = float(ELEMENTS[-3].radii[int(radiustype)])
                    color = ELEMENTS[-3].color
                # ... take what is written in the PDB file. These are somewhat
                # unknown atoms. This should never happen, the element list is
                # almost complete. However, we do this due to security reasons.
                else:
                    short_name = str.upper(short_name)
                    name = str.upper(short_name)
                    radius = float(ELEMENTS[-2].radii[int(radiustype)])
                    color = ELEMENTS[-2].color

            # x,y and z are at fixed positions in the PDB file.
            x = float(line[30:38].rsplit()[0])
            y = float(line[38:46].rsplit()[0])
            z = float(line[46:55].rsplit()[0])

            location = Vector((x,y,z))

            j += 1

            # Append the atom to the list. Material remains empty so far.
            all_atoms.append(AtomProp(short_name,
                                      name,
                                      location,
                                      radius,
                                      color,[]))

        line = filepath_pdb_p.readline()
        line = line[:-1]

    filepath_pdb_p.close()
    # From above it can be clearly seen that j is now the number of all atoms.
    Number_of_total_atoms = j

    return (Number_of_total_atoms, all_atoms)


# The function, which reads the sticks in a PDB file.
def read_pdb_file_sticks(filepath_pdb, use_sticks_bonds, all_atoms):

    # The list of all sticks.
    all_sticks = []

    # Open the PDB file.
    filepath_pdb_p = open(filepath_pdb, "r")

    line = filepath_pdb_p.readline()
    split_list = line.split(' ')

    # Go to the first entry
    # DO NOT CHANGE 'CONECT', read below.
    if "CONECT" not in split_list[0]:
        for line in filepath_pdb_p:
            split_list = line.split(' ')
            if "CONECT" in split_list[0]:
                break

    Number_of_sticks = 0
    sticks_double = 0
    j = 0
    # This is in fact an endless while loop, ...
    while j > -1:

        # ... which is broken here (EOF) ...
        if line == "":
            break
        # ... or here, when no 'CONECT' appears anymore.
        if "CONECT" not in line:
            break

        # Note 2019-03-16: in a PDB file the identifier for sticks is called
        # 'CONECT' and NOT 'CONNECT'! Please leave this as is, otherwise the
        # sticks are NOT correctly imported.

        # The strings of the atom numbers do have a clear position in the file
        # (From 7 to 12, from 13 to 18 and so on.) and one needs to consider
        # this. One could also use the split function but then one gets into
        # trouble if there are lots of atoms: For instance, it may happen that
        # one has
        #                   CONECT 11111  22244444
        #
        # In Fact it means that atom No. 11111 has a connection with atom
        # No. 222 but also with atom No. 44444. The split function would give
        # me only two numbers (11111 and 22244444), which is wrong.

        # Cut spaces from the right and 'CONECT' at the beginning
        line = line.rstrip()
        line = line[6:]
        # Amount of loops
        length = len(line)
        loops  = int(length/5)

        # List of atoms
        atom_list = []
        for i in range(loops):
            number = line[5*i:5*(i+1)].rsplit()
            if number != []:
                if number[0].isdigit() == True:
                    atom_number = int(number[0])
                    atom_list.append(atom_number)

        # The first atom is connected with all the others in the list.
        atom1 = atom_list[0]

        # For all the other atoms in the list do:
        for atom2 in atom_list[1:]:

            if use_sticks_bonds == True:
                number = atom_list[1:].count(atom2)

                if number == 2 or number == 3:
                    basis_list = list(set(atom_list[1:]))

                    if len(basis_list) > 1:
                        basis1 = (all_atoms[atom1-1].location
                                - all_atoms[basis_list[0]-1].location)
                        basis2 = (all_atoms[atom1-1].location
                                - all_atoms[basis_list[1]-1].location)
                        plane_n = basis1.cross(basis2)

                        dist_n = (all_atoms[atom1-1].location
                                - all_atoms[atom2-1].location)
                        dist_n = dist_n.cross(plane_n)
                        dist_n = dist_n / dist_n.length
                    else:
                        dist_n = (all_atoms[atom1-1].location
                                - all_atoms[atom2-1].location)
                        dist_n = Vector((dist_n[1],-dist_n[0],0))
                        dist_n = dist_n / dist_n.length

                elif number > 3:
                    number = 1
                    dist_n = None
                else:
                    dist_n = None
            else:
                number = 1
                dist_n = None

            # Note that in a PDB file, sticks of one atom pair can appear a
            # couple of times. (Only god knows why ...)
            # So, does a stick between the considered atoms already exist?
            FLAG_BAR = False
            for k in range(Number_of_sticks):
                if ((all_sticks[k].atom1 == atom1 and all_sticks[k].atom2 == atom2) or
                    (all_sticks[k].atom2 == atom1 and all_sticks[k].atom1 == atom2)):
                    sticks_double += 1
                    # If yes, then FLAG on 'True'.
                    FLAG_BAR       = True
                    break

            # If the stick is not yet registered (FLAG_BAR == False), then
            # register it!
            if FLAG_BAR == False:
                all_sticks.append(StickProp(atom1,atom2,number,dist_n))
                Number_of_sticks += 1
                j += 1

        line = filepath_pdb_p.readline()
        line = line.rstrip()

    filepath_pdb_p.close()

    return all_sticks


# Function, which produces a cylinder. All is somewhat easy to understand.
def build_stick(radius, length, sectors, element_name):

    dphi = 2.0 * pi/(float(sectors)-1)

    # Vertices
    vertices_top    = [Vector((0,0,length / 2.0))]
    vertices_bottom = [Vector((0,0,-length / 2.0))]
    vertices = []
    for i in range(sectors-1):
        x = radius * cos( dphi * i )
        y = radius * sin( dphi * i )
        z =  length / 2.0
        vertex = Vector((x,y,z))
        vertices_top.append(vertex)
        z = -length / 2.0
        vertex = Vector((x,y,z))
        vertices_bottom.append(vertex)
    vertices = vertices_top + vertices_bottom

    # Side facets (Cylinder)
    faces1 = []
    for i in range(sectors-1):
        if i == sectors-2:
            faces1.append(  [i+1, 1, 1+sectors, i+1+sectors] )
        else:
            faces1.append(  [i+1, i+2, i+2+sectors, i+1+sectors] )

    # Top facets
    faces2 = []
    for i in range(sectors-1):
        if i == sectors-2:
            face_top = [0,sectors-1,1]
            face_bottom = [sectors,2*sectors-1,sectors+1]
        else:
            face_top    = [0]
            face_bottom = [sectors]
            for j in range(2):
                face_top.append(i+j+1)
                face_bottom.append(i+j+1+sectors)
        faces2.append(face_top)
        faces2.append(face_bottom)

    # Build the mesh, Cylinder
    cylinder = bpy.data.meshes.new(element_name+"_sticks_cylinder")
    cylinder.from_pydata(vertices, [], faces1)
    cylinder.update()
    new_cylinder = bpy.data.objects.new(element_name+"_sticks_cylinder", cylinder)
    # Attention: the linking will be done a few moments later, after this
    # is done definition.

    # Build the mesh, Cups
    cups = bpy.data.meshes.new(element_name+"_sticks_cup")
    cups.from_pydata(vertices, [], faces2)
    cups.update()
    new_cups = bpy.data.objects.new(element_name+"_sticks_cup", cups)
    # Attention: the linking will be done a few moments later, after this
    # is done definition.

    return new_cylinder, new_cups


# Rotate an object.
def rotate_object(rot_mat, obj):

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    # Decompose world_matrix's components, and from them assemble 4x4 matrices.
    orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()

    orig_loc_mat   = Matrix.Translation(orig_loc)
    orig_rot_mat   = orig_rot.to_matrix().to_4x4()
    orig_scale_mat = (Matrix.Scale(orig_scale[0],4,(1,0,0)) @
                      Matrix.Scale(orig_scale[1],4,(0,1,0)) @
                      Matrix.Scale(orig_scale[2],4,(0,0,1)))

    # Assemble the new matrix.
    obj.matrix_world = orig_loc_mat @ rot_mat @ orig_rot_mat @ orig_scale_mat


# Function, which puts a camera and light source into the 3D scene
def camera_light_source(use_camera,
                        use_light,
                        object_center_vec,
                        object_size):

    camera_factor = 15.0

    # If chosen, a camera is put into the scene.
    if use_camera == True:

        # Assume that the object is put into the global origin. Then, the
        # camera is moved in x and z direction, not in y. The object has its
        # size at distance sqrt(object_size) from the origin. So, move the
        # camera by this distance times a factor of camera_factor in x and z.
        # Then add x, y and z of the origin of the object.
        object_camera_vec = Vector((sqrt(object_size) * camera_factor,
                                    0.0,
                                    sqrt(object_size) * camera_factor))
        camera_xyz_vec = object_center_vec + object_camera_vec

        # Create the camera
        camera_data = bpy.data.cameras.new("A_camera")
        camera_data.lens = 45
        camera_data.clip_end = 500.0
        camera = bpy.data.objects.new("A_camera", camera_data)
        camera.location = camera_xyz_vec
        bpy.context.collection.objects.link(camera)

        # Here the camera is rotated such it looks towards the center of
        # the object. The [0.0, 0.0, 1.0] vector along the z axis
        z_axis_vec             = Vector((0.0, 0.0, 1.0))
        # The angle between the last two vectors
        angle                  = object_camera_vec.angle(z_axis_vec, 0)
        # The cross-product of z_axis_vec and object_camera_vec
        axis_vec               = z_axis_vec.cross(object_camera_vec)
        # Rotate 'axis_vec' by 'angle' and convert this to euler parameters.
        # 4 is the size of the matrix.
        camera.rotation_euler  = Matrix.Rotation(angle, 4, axis_vec).to_euler()

        # Rotate the camera around its axis by 90° such that we have a nice
        # camera position and view onto the object.
        bpy.ops.object.select_all(action='DESELECT')
        camera.select_set(True)

        # Rotate the camera around its axis 'object_camera_vec' by 90° such
        # that we have a nice camera view onto the object.
        matrix_rotation = Matrix.Rotation(90/360*2*pi, 4, object_camera_vec)
        rotate_object(matrix_rotation, camera)

    # Here a lamp is put into the scene, if chosen.
    if use_light == True:

        # This is the distance from the object measured in terms of %
        # of the camera distance. It is set onto 50% (1/2) distance.
        lamp_dl = sqrt(object_size) * 15 * 0.5
        # This is a factor to which extend the lamp shall go to the right
        # (from the camera  point of view).
        lamp_dy_right = lamp_dl * (3.0/4.0)

        # Create x, y and z for the lamp.
        object_lamp_vec = Vector((lamp_dl,lamp_dy_right,lamp_dl))
        lamp_xyz_vec = object_center_vec + object_lamp_vec
        length = lamp_xyz_vec.length

        # As a lamp we use a point source.
        lamp_data = bpy.data.lights.new(name="A_lamp", type="POINT")
        # We now determine the emission strength of the lamp. Note that the
        # intensity depends on 1/r^2. For this we use a value of 100000.0 at a
        # distance of 58. This value was determined manually inside Blender.
        lamp_data.energy = 500000.0 * ( (length * length) / (58.0 * 58.0) )
        lamp = bpy.data.objects.new("A_lamp", lamp_data)
        lamp.location = lamp_xyz_vec
        bpy.context.collection.objects.link(lamp)

        # Some settings for the World: a bit ambient occlusion
        bpy.context.scene.world.light_settings.use_ambient_occlusion = True
        bpy.context.scene.world.light_settings.ao_factor = 0.1



# Function, which draws the atoms of one type (balls). This is one
# dupliverts structure then.
# Return: the dupliverts structure
def draw_atoms_one_type(draw_all_atoms_type,
                        Ball_type,
                        Ball_azimuth,
                        Ball_zenith,
                        Ball_radius_factor,
                        object_center_vec,
                        collection_molecule):

    # Create the vertices composed of the coordinates of all atoms of one type
    atom_vertices = []
    for atom in draw_all_atoms_type:
        # In fact, the object is created in the World's origin.
        # This is why 'object_center_vec' is subtracted. At the end
        # the whole object is translated back to 'object_center_vec'.
        atom_vertices.append(atom[2] - object_center_vec)

    # IMPORTANT: First, we create a collection of the element, which contains
    # the atoms (balls + mesh) AND the sticks! The definition dealing with the
    # sticks will put the sticks inside this collection later on.
    coll_element_name = atom[0] # the element name
    # Create the new collection and ...
    coll_element = bpy.data.collections.new(coll_element_name)
    # ... link it to the collection, which contains all parts of the
    # molecule.
    collection_molecule.children.link(coll_element)

    # Now, create a collection for the atoms, which includes the representative
    # ball and the mesh.
    coll_atom_name = atom[0] + "_atom"
    # Create the new collection and ...
    coll_atom = bpy.data.collections.new(coll_atom_name)
    # ... link it to the collection, which contains all parts of the
    # element (ball and mesh).
    coll_element.children.link(coll_atom)

    # Build the mesh
    atom_mesh = bpy.data.meshes.new("Mesh_"+atom[0])
    atom_mesh.from_pydata(atom_vertices, [], [])
    atom_mesh.update()
    new_atom_mesh = bpy.data.objects.new(atom[0] + "_mesh", atom_mesh)

    # Link active object to the new collection
    coll_atom.objects.link(new_atom_mesh)

    # Now, build a representative sphere (atom).
    if atom[0] == "Vacancy":
        bpy.ops.mesh.primitive_cube_add(
                        align='WORLD', enter_editmode=False,
                        location=(0.0, 0.0, 0.0),
                        rotation=(0.0, 0.0, 0.0))
    else:
        # NURBS balls
        if Ball_type == "0":
            bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                        align='WORLD', enter_editmode=False,
                        location=(0,0,0), rotation=(0.0, 0.0, 0.0))
        # UV balls
        elif Ball_type == "1":
            bpy.ops.mesh.primitive_uv_sphere_add(
                        segments=Ball_azimuth, ring_count=Ball_zenith,
                        align='WORLD', enter_editmode=False,
                        location=(0,0,0), rotation=(0, 0, 0))
        # Meta balls
        elif Ball_type == "2":
            bpy.ops.object.metaball_add(type='BALL', align='WORLD',
                        enter_editmode=False, location=(0, 0, 0),
                        rotation=(0, 0, 0))

    ball = bpy.context.view_layer.objects.active
    # Hide this ball because its appearance has no meaning. It is just the
    # representative ball. The ball is visible at the vertices of the mesh.
    # Rememmber, this is a dupliverts construct!
    # However, hiding does not work with meta balls!
    if Ball_type == "0" or Ball_type == "1":
        ball.hide_set(True)
    # Scale up/down the ball radius.
    ball.scale  = (atom[3]*Ball_radius_factor,) * 3

    if atom[0] == "Vacancy":
        ball.name = atom[0] + "_cube"
    else:
        ball.name = atom[0] + "_ball"

    ball.active_material = atom[1]
    ball.parent = new_atom_mesh
    new_atom_mesh.instance_type = 'VERTS'
    # The object is back translated to 'object_center_vec'.
    new_atom_mesh.location = object_center_vec

    # Note the collection where the ball was placed into.
    coll_all = ball.users_collection
    if len(coll_all) > 0:
        coll_past = coll_all[0]
    else:
        coll_past = bpy.context.scene.collection

    # Put the atom into the new collection 'atom' and ...
    coll_atom.objects.link(ball)
    # ... unlink the atom from the other collection.
    coll_past.objects.unlink(ball)

    return new_atom_mesh, coll_element


# Function, which draws the sticks with help of the dupliverts technique.
# Return: list of dupliverts structures.
def draw_sticks_dupliverts(all_atoms,
                           atom_all_types_list,
                           center,
                           all_sticks,
                           Stick_diameter,
                           Stick_sectors,
                           Stick_unit,
                           Stick_dist,
                           use_sticks_smooth,
                           use_sticks_color,
                           list_coll_elements):

    dl = Stick_unit

    if use_sticks_color == False:
        stick_material = bpy.data.materials.new(ELEMENTS[-1].name)
        stick_material.use_nodes = True
        mat_P_BSDF = next(n for n in stick_material.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = ELEMENTS[-1].color

    # Sort the sticks and put them into a new list such that ...
    sticks_all_lists = []
    if use_sticks_color == True:
        for atom_type in atom_all_types_list:
            if atom_type[0] == "TER":
                continue
            sticks_list = []
            for stick in all_sticks:
                for repeat in range(stick.number):

                    atom1 = copy(all_atoms[stick.atom1-1].location)-center
                    atom2 = copy(all_atoms[stick.atom2-1].location)-center

                    dist =  Stick_diameter * Stick_dist

                    if stick.number == 2:
                        if repeat == 0:
                            atom1 += (stick.dist * dist)
                            atom2 += (stick.dist * dist)
                        if repeat == 1:
                            atom1 -= (stick.dist * dist)
                            atom2 -= (stick.dist * dist)

                    if stick.number == 3:
                        if repeat == 0:
                            atom1 += (stick.dist * dist)
                            atom2 += (stick.dist * dist)
                        if repeat == 2:
                            atom1 -= (stick.dist * dist)
                            atom2 -= (stick.dist * dist)

                    dv = atom1 - atom2
                    n  = dv / dv.length
                    if atom_type[0] == all_atoms[stick.atom1-1].name:
                        location = atom1
                        name     = "_" + all_atoms[stick.atom1-1].name
                        material = all_atoms[stick.atom1-1].material
                        sticks_list.append([name, location, dv, material])
                    if atom_type[0] == all_atoms[stick.atom2-1].name:
                        location = atom1 - n * dl * int(ceil(dv.length / (2.0 * dl)))
                        name     = "_" + all_atoms[stick.atom2-1].name
                        material = all_atoms[stick.atom2-1].material
                        sticks_list.append([name, location, dv, material])

            if sticks_list != []:
                sticks_all_lists.append(sticks_list)
    else:
        sticks_list = []
        for stick in all_sticks:

            if stick.number > 3:
                stick.number = 1

            for repeat in range(stick.number):

                atom1 = copy(all_atoms[stick.atom1-1].location)-center
                atom2 = copy(all_atoms[stick.atom2-1].location)-center

                dist =  Stick_diameter * Stick_dist

                if stick.number == 2:
                    if repeat == 0:
                        atom1 += (stick.dist * dist)
                        atom2 += (stick.dist * dist)
                    if repeat == 1:
                        atom1 -= (stick.dist * dist)
                        atom2 -= (stick.dist * dist)
                if stick.number == 3:
                    if repeat == 0:
                        atom1 += (stick.dist * dist)
                        atom2 += (stick.dist * dist)
                    if repeat == 2:
                        atom1 -= (stick.dist * dist)
                        atom2 -= (stick.dist * dist)

                dv = atom1 - atom2
                n  = dv / dv.length
                location = atom1
                material = stick_material
                sticks_list.append(["", location, dv, material])

        sticks_all_lists.append(sticks_list)

    atom_object_list = []
    # ... the sticks in the list can be drawn:
    for stick_list in sticks_all_lists:
        vertices = []
        faces    = []
        i = 0

        # What follows is school mathematics! :-) We construct equidistant
        # planes, on which the stick sections (cylinders) are perpendicular on.
        for stick in stick_list:

            dv = stick[2]
            v1 = stick[1]
            n  = dv / dv.length
            gamma = -n.dot(v1)
            b     = v1 + gamma * n
            n_b   = b / b.length

            if use_sticks_color == True:
                loops = int(ceil(dv.length / (2.0 * dl)))
            else:
                loops = int(ceil(dv.length / dl))

            for j in range(loops):

                # The plane, which is normal to the length of the cylinder,
                # will have a 1/100 of the stick diameter. => When decreasing
                # the size of the stick diameter, the plane will not be visible.
                f = 0.01
                g  = v1 - n * dl / 2.0 - n * dl * j
                p1 = g + n_b * Stick_diameter * f
                p2 = g - n_b * Stick_diameter * f
                p3 = g - n_b.cross(n) * Stick_diameter * f
                p4 = g + n_b.cross(n) * Stick_diameter * f

                vertices.append(p1)
                vertices.append(p2)
                vertices.append(p3)
                vertices.append(p4)
                faces.append((i*4+0,i*4+2,i*4+1,i*4+3))
                i += 1

        # Create a collection for the sticks, which includes the representative
        # cylinders, cups and the mesh.
        coll_name = stick[0][1:] + "_sticks"
        # Create the collection and ...
        coll = bpy.data.collections.new(coll_name)
        # ... link it to the collection, which contains all parts of the
        # element. 'stick[0][1:]' contains the name of the element!
        for coll_element_from_list in list_coll_elements:
            if stick[0][1:] in coll_element_from_list.name:
                break
        coll_element_from_list.children.link(coll)

        # Build the mesh.
        mesh = bpy.data.meshes.new("Sticks_"+stick[0][1:])
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        new_mesh = bpy.data.objects.new(stick[0][1:]+"_sticks_mesh", mesh)
        # Link active object to the new collection
        coll.objects.link(new_mesh)

        # Build the object. Get the cylinder from the 'build_stick' function.
        stick_cylinder, stick_cups = build_stick(Stick_diameter,
                                                 dl,
                                                 Stick_sectors,
                                                 stick[0][1:])
        # Link active object to the new collection.
        coll.objects.link(stick_cylinder)
        coll.objects.link(stick_cups)

        # Assign the material.
        stick_cylinder.active_material = stick[3]
        stick_cups.active_material = stick[3]

        # Smooth the cylinders.
        if use_sticks_smooth == True:
            bpy.ops.object.select_all(action='DESELECT')
            stick_cylinder.select_set(True)
            stick_cups.select_set(True)
            bpy.ops.object.shade_smooth()

        # Hide these objects because their appearance has no meaning. They are
        # just the representative objects. The cylinder and cups are visible at
        # the vertices of the mesh. Rememmber, this is a dupliverts construct!
        stick_cylinder.hide_set(True)
        stick_cups.hide_set(True)

        # Parenting the mesh to the cylinder.
        stick_cylinder.parent = new_mesh
        stick_cups.parent = new_mesh
        new_mesh.instance_type = 'FACES'
        new_mesh.location = center
        atom_object_list.append(new_mesh)

    # Return the list of dupliverts structures.
    return atom_object_list


# Function, which draws the sticks with help of the skin and subdivision
# modifiers.
def draw_sticks_skin(all_atoms,
                     all_sticks,
                     Stick_diameter,
                     use_sticks_smooth,
                     sticks_subdiv_view,
                     sticks_subdiv_render,
                     coll_molecule):

    # These counters are for the edges, in the shape [i,i+1].
    i = 0

    # This is the list of vertices, containing the atom position
    # (vectors)).
    stick_vertices = []
    # This is the 'same' list, which contains not vector position of
    # the atoms but their numbers. It is used to handle the edges.
    stick_vertices_nr = []
    # This is the list of edges.
    stick_edges = []

    # Go through the list of all sticks. For each stick do:
    for stick in all_sticks:

        # Each stick has two atoms = two vertices.

        """
        [ 0,1 ,  3,4 ,  0,8 ,  7,3]
        [[0,1], [2,3], [4,5], [6,7]]

        [ 0,1 ,  3,4 ,  x,8 ,   7,x]    x:deleted
        [[0,1], [2,3], [0,5], [6,2]]
        """

        # Check, if the vertex (atom) is already in the vertex list.
        # edge: [s1,s2]
        FLAG_s1 = False
        s1 = 0
        for stick2 in stick_vertices_nr:
            if stick2 == stick.atom1-1:
                FLAG_s1 = True
                break
            s1 += 1
        FLAG_s2 = False
        s2 = 0
        for stick2 in stick_vertices_nr:
            if stick2 == stick.atom2-1:
                FLAG_s2 = True
                break
            s2 += 1

        # If the vertex (atom) is not yet in the vertex list:
        # append the number of atom and the vertex to the two lists.
        # For the first atom:
        if FLAG_s1 == False:
            atom1 = copy(all_atoms[stick.atom1-1].location)
            stick_vertices.append(atom1)
            stick_vertices_nr.append(stick.atom1-1)
        # For the second atom:
        if FLAG_s2 == False:
            atom2 = copy(all_atoms[stick.atom2-1].location)
            stick_vertices.append(atom2)
            stick_vertices_nr.append(stick.atom2-1)

        # Build the edges:

        # If both vertices (atoms) were not in the lists, then
        # the edge is simply [i,i+1]. These are two new vertices
        # (atoms), so increase i by 2.
        if FLAG_s1 == False and FLAG_s2 == False:
            stick_edges.append([i,i+1])
            i += 2
        # Both vertices (atoms) were already in the list, so then
        # use the vertices (atoms), which already exist. They are
        # at positions s1 and s2.
        if FLAG_s1 == True and FLAG_s2 == True:
            stick_edges.append([s1,s2])
        # The following two if cases describe the situation that
        # only one vertex (atom) was in the list. Since only ONE
        # new vertex was added, increase i by one.
        if FLAG_s1 == True and FLAG_s2 == False:
            stick_edges.append([s1,i])
            i += 1
        if FLAG_s1 == False and FLAG_s2 == True:
            stick_edges.append([i,s2])
            i += 1

    # Build the mesh of the sticks
    stick_mesh = bpy.data.meshes.new("Mesh_sticks")
    stick_mesh.from_pydata(stick_vertices, stick_edges, [])
    stick_mesh.update()
    new_stick_mesh = bpy.data.objects.new("Sticks", stick_mesh)
    # Link the active mesh to the molecule collection
    coll_molecule.objects.link(new_stick_mesh)

    # Apply the skin modifier.
    new_stick_mesh.modifiers.new(name="Sticks_skin", type='SKIN')
    # Smooth the skin surface if this option has been chosen.
    new_stick_mesh.modifiers[0].use_smooth_shade = use_sticks_smooth
    # Apply the Subdivision modifier.
    new_stick_mesh.modifiers.new(name="Sticks_subsurf", type='SUBSURF')
    # Options: choose the levels
    new_stick_mesh.modifiers[1].levels = sticks_subdiv_view
    new_stick_mesh.modifiers[1].render_levels = sticks_subdiv_render

    stick_material = bpy.data.materials.new(ELEMENTS[-1].name)
    stick_material.use_nodes = True
    mat_P_BSDF = next(n for n in stick_material.node_tree.nodes
                      if n.type == "BSDF_PRINCIPLED")
    mat_P_BSDF.inputs['Base Color'].default_value = ELEMENTS[-1].color
    new_stick_mesh.active_material = stick_material

    # This is for putting the radius of the sticks onto
    # the desired value 'Stick_diameter'
    bpy.context.view_layer.objects.active = new_stick_mesh
    # EDIT mode
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bm = bmesh.from_edit_mesh(new_stick_mesh.data)
    bpy.ops.mesh.select_all(action='DESELECT')

    # Select all vertices
    for v in bm.verts:
        v.select = True

    # This is somewhat a factor for the radius.
    r_f = 4.0
    # Apply operator 'skin_resize'.
    bpy.ops.transform.skin_resize(
        value=(
            Stick_diameter * r_f,
            Stick_diameter * r_f,
            Stick_diameter * r_f,
        ),
        constraint_axis=(False, False, False),
        orient_type='GLOBAL',
        mirror=False,
        use_proportional_edit=False,
        snap=False,
        snap_target='CLOSEST',
        snap_point=(0, 0, 0),
        snap_align=False,
        snap_normal=(0, 0, 0),
        release_confirm=False,
    )
    # Back to the OBJECT mode.
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    return new_stick_mesh


# Draw the sticks the normal way: connect the atoms by simple cylinders.
# Two options: 1. single cylinders parented to an empty
#              2. one single mesh object
def draw_sticks_normal(all_atoms,
                       all_sticks,
                       center,
                       Stick_diameter,
                       Stick_sectors,
                       Stick_dist,
                       use_sticks_smooth,
                       use_sticks_one_object,
                       use_sticks_one_object_nr,
                       coll_molecule):

    stick_material = bpy.data.materials.new(ELEMENTS[-1].name)
    stick_material.use_nodes = True
    mat_P_BSDF = next(n for n in stick_material.node_tree.nodes
                      if n.type == "BSDF_PRINCIPLED")
    mat_P_BSDF.inputs['Base Color'].default_value = ELEMENTS[-1].color

    up_axis = Vector([0.0, 0.0, 1.0])

    # For all sticks, do ...
    list_group = []
    list_group_sub = []
    counter = 0
    for i, stick in enumerate(all_sticks):

        # We treat here single, double and tripple bonds: stick.number <= 3
        for repeat in range(stick.number):

            # The vectors of the two atoms
            atom1 = copy(all_atoms[stick.atom1-1].location)-center
            atom2 = copy(all_atoms[stick.atom2-1].location)-center

            dist =  Stick_diameter * Stick_dist

            # The two sticks are on the left and right of the middle connection.
            if stick.number == 2:
                if repeat == 0:
                    atom1 += (stick.dist * dist)
                    atom2 += (stick.dist * dist)
                if repeat == 1:
                    atom1 -= (stick.dist * dist)
                    atom2 -= (stick.dist * dist)

            if stick.number == 3:
                if repeat == 0:
                    atom1 += (stick.dist * dist)
                    atom2 += (stick.dist * dist)
                if repeat == 2:
                    atom1 -= (stick.dist * dist)
                    atom2 -= (stick.dist * dist)

            # Vector pointing along the stick direction
            dv = atom1 - atom2
            # The normalized vector of this, with lenght 1
            n  = dv / dv.length
            # Starting point of the stick
            location = (atom1 + atom2) * 0.5
            # Angle with respect to the z-axis
            angle = dv.angle(up_axis, 0)
            # Cross-product between v and the z-axis vector. It is the
            # vector of rotation.
            axis = up_axis.cross(dv)
            # Calculate Euler angles
            euler = Matrix.Rotation(angle, 4, axis).to_euler()
            # Create stick
            stick_obj = bpy.ops.mesh.primitive_cylinder_add(vertices=Stick_sectors,
                                                            radius=Stick_diameter,
                                                            depth=dv.length,
                                                            end_fill_type='NGON',
                                                            align='WORLD',
                                                            enter_editmode=False,
                                                            location=location,
                                                            rotation=(0, 0, 0))
            # Put the stick into the scene ...
            stick_obj = bpy.context.view_layer.objects.active
            # ... and rotate the stick.
            stick_obj.rotation_euler = euler
            # ... and name
            if stick.number == 1:
                stick_obj.name = "Stick_Cylinder_%04d" %(i)
            elif stick.number == 2:
                if repeat == 0:
                    stick_obj.name = "Stick_Cylinder_%04d" %(i) + "_left"
                elif repeat == 1:
                    stick_obj.name = "Stick_Cylinder_%04d" %(i) + "_right"
            elif stick.number == 3:
                if repeat == 0:
                    stick_obj.name = "Stick_Cylinder_%04d" %(i) + "_left"
                elif repeat == 1:
                    stick_obj.name = "Stick_Cylinder_%04d" %(i) + "_middle"
                elif repeat == 2:
                    stick_obj.name = "Stick_Cylinder_%04d" %(i) + "_right"
                # Never occurs:
                else:
                    stick_obj.name = "Stick_Cylinder"
            # Never occurs:
            else:
                stick_obj.name = "Stick_Cylinder"
            counter += 1

            # Smooth the cylinder.
            if use_sticks_smooth == True:
                bpy.ops.object.select_all(action='DESELECT')
                stick_obj.select_set(True)
                bpy.ops.object.shade_smooth()

            list_group_sub.append(stick_obj)

            if use_sticks_one_object == True:
                if counter == use_sticks_one_object_nr:
                    bpy.ops.object.select_all(action='DESELECT')
                    for stick_select in list_group_sub:
                        stick_select.select_set(True)
                    bpy.ops.object.join()
                    list_group.append(bpy.context.view_layer.objects.active)
                    bpy.ops.object.select_all(action='DESELECT')
                    list_group_sub = []
                    counter = 0
            else:
                # Material ...
                stick_obj.active_material = stick_material

    if use_sticks_one_object == True:
        bpy.ops.object.select_all(action='DESELECT')
        for stick in list_group_sub:
            stick.select_set(True)
        bpy.ops.object.join()
        list_group.append(bpy.context.view_layer.objects.active)
        bpy.ops.object.select_all(action='DESELECT')

        for group in list_group:
            group.select_set(True)
        bpy.ops.object.join()
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',
                                  center='MEDIAN')
        sticks = bpy.context.view_layer.objects.active
        sticks.active_material = stick_material

        sticks.location += center

        # Collections
        # ===========
        # Note the collection where the sticks were placed into.
        coll_all = sticks.users_collection
        if len(coll_all) > 0:
            coll_past = coll_all[0]
        else:
            coll_past = bpy.context.scene.collection

        # Link the sticks with the collection of the molecule ...
        coll_molecule.objects.link(sticks)
        # ... and unlink them from the collection it has been before.
        coll_past.objects.unlink(sticks)

        return sticks
    else:
        # Here we use an empty ...
        bpy.ops.object.empty_add(type='ARROWS',
                                  align='WORLD',
                                  location=(0, 0, 0),
                                  rotation=(0, 0, 0))
        sticks_empty = bpy.context.view_layer.objects.active
        sticks_empty.name = "A_sticks_empty"
        # ... that is parent to all sticks. With this, we can better move
        # all sticks if necessary.
        for stick in list_group_sub:
            stick.parent = sticks_empty

        sticks_empty.location += center

        # Collections
        # ===========
        # Create a collection that will contain all sticks + the empty and ...
        coll = bpy.data.collections.new("Sticks")
        # ... link it to the collection, which contains all parts of the
        # molecule.
        coll_molecule.children.link(coll)
        # Now, create a collection that only contains the sticks and ...
        coll_cylinder = bpy.data.collections.new("Sticks_cylinders")
        # ... link it to the collection, which contains the sticks and empty.
        coll.children.link(coll_cylinder)

        # Note the collection where the empty was placed into, ...
        coll_all = sticks_empty.users_collection
        if len(coll_all) > 0:
            coll_past = coll_all[0]
        else:
            coll_past = bpy.context.scene.collection
        # ... link the empty with the new collection  ...
        coll.objects.link(sticks_empty)
        # ... and unlink it from the old collection where it has been before.
        coll_past.objects.unlink(sticks_empty)

        # Note the collection where the cylinders were placed into, ...
        coll_all = list_group_sub[0].users_collection
        if len(coll_all) > 0:
            coll_past = coll_all[0]
        else:
            coll_past = bpy.context.scene.collection

        for stick in list_group_sub:
            # ... link each stick with the new collection  ...
            coll_cylinder.objects.link(stick)
            # ... and unlink it from the old collection.
            coll_past.objects.unlink(stick)

        return sticks_empty


# -----------------------------------------------------------------------------
#                                                            The main routine

def import_pdb(Ball_type,
               Ball_azimuth,
               Ball_zenith,
               Ball_radius_factor,
               radiustype,
               Ball_distance_factor,
               use_sticks,
               use_sticks_type,
               sticks_subdiv_view,
               sticks_subdiv_render,
               use_sticks_color,
               use_sticks_smooth,
               use_sticks_bonds,
               use_sticks_one_object,
               use_sticks_one_object_nr,
               Stick_unit, Stick_dist,
               Stick_sectors,
               Stick_diameter,
               put_to_center,
               use_camera,
               use_light,
               filepath_pdb):

    # List of materials
    atom_material_list = []

    # A list of ALL objects which are loaded (needed for selecting the loaded
    # structure.
    atom_object_list = []

    # ------------------------------------------------------------------------
    # INITIALIZE THE ELEMENT LIST

    read_elements()

    # ------------------------------------------------------------------------
    # READING DATA OF ATOMS

    (Number_of_total_atoms, all_atoms) = read_pdb_file(filepath_pdb, radiustype)

    # ------------------------------------------------------------------------
    # MATERIAL PROPERTIES FOR ATOMS

    # The list that contains info about all types of atoms is created
    # here. It is used for building the material properties for
    # instance (see below).
    atom_all_types_list = []

    for atom in all_atoms:
        FLAG_FOUND = False
        for atom_type in atom_all_types_list:
            # If the atom name is already in the list, FLAG on 'True'.
            if atom_type[0] == atom.name:
                FLAG_FOUND = True
                break
        # No name in the current list has been found? => New entry.
        if FLAG_FOUND == False:
            # Stored are: Atom label (e.g. 'Na'), the corresponding atom
            # name (e.g. 'Sodium') and its color.
            atom_all_types_list.append([atom.name, atom.element, atom.color])

    # The list of materials is built.
    # Note that all atoms of one type (e.g. all hydrogens) get only ONE
    # material! This is good because then, by activating one atom in the
    # Blender scene and changing the color of this atom, one changes the color
    # of ALL atoms of the same type at the same time.

    # Create first a new list of materials for each type of atom
    # (e.g. hydrogen)
    for atom_type in atom_all_types_list:
        material = bpy.data.materials.new(atom_type[1])
        material.diffuse_color = atom_type[2]
        material.use_nodes = True
        mat_P_BSDF = next(n for n in material.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = atom_type[2]
        material.name = atom_type[0]
        atom_material_list.append(material)

    # Now, we go through all atoms and give them a material. For all atoms ...
    for atom in all_atoms:
        # ... and all materials ...
        for material in atom_material_list:
            # ... select the correct material for the current atom via
            # comparison of names ...
            if atom.name in material.name:
                # ... and give the atom its material properties.
                # However, before we check if it is a vacancy.
                # The vacancy is represented by a transparent cube.
                if atom.name == "Vacancy":
                    # For cycles and eevee.
                    material.use_nodes = True
                    mat_P_BSDF = next(n for n in material.node_tree.nodes
                                      if n.type == "BSDF_PRINCIPLED")
                    mat_P_BSDF.inputs['Metallic'].default_value = 0.1
                    mat_P_BSDF.inputs['Specular'].default_value = 0.15
                    mat_P_BSDF.inputs['Roughness'].default_value = 0.05
                    mat_P_BSDF.inputs['Clearcoat Roughness'].default_value = 0.37
                    mat_P_BSDF.inputs['IOR'].default_value = 0.8
                    mat_P_BSDF.inputs['Transmission'].default_value = 0.6
                    mat_P_BSDF.inputs['Transmission Roughness'].default_value = 0.0
                    mat_P_BSDF.inputs['Alpha'].default_value = 0.5
                    # Some additional stuff for eevee.
                    material.blend_method = 'HASHED'
                    material.shadow_method = 'HASHED'
                    material.use_backface_culling = False
                # The atom gets its properties.
                atom.material = material

    # ------------------------------------------------------------------------
    # READING DATA OF STICKS

    all_sticks = read_pdb_file_sticks(filepath_pdb,
                                      use_sticks_bonds,
                                      all_atoms)
    #
    # So far, all atoms, sticks and materials have been registered.
    #

    # ------------------------------------------------------------------------
    # TRANSLATION OF THE STRUCTURE TO THE ORIGIN

    # It may happen that the structure in a PDB file already has an offset
    # If chosen, the structure is first put into the center of the scene
    # (the offset is subtracted).

    if put_to_center == True:
        sum_vec = Vector((0.0,0.0,0.0))
        # Sum of all atom coordinates
        sum_vec = sum([atom.location for atom in all_atoms], sum_vec)
        # Then the average is taken
        sum_vec = sum_vec / Number_of_total_atoms
        # After, for each atom the center of gravity is subtracted
        for atom in all_atoms:
            atom.location -= sum_vec

    # ------------------------------------------------------------------------
    # SCALING

    # Take all atoms and adjust their radii and scale the distances.
    for atom in all_atoms:
        atom.location *= Ball_distance_factor

    # ------------------------------------------------------------------------
    # DETERMINATION OF SOME GEOMETRIC PROPERTIES

    # In the following, some geometric properties of the whole object are
    # determined: center, size, etc.
    sum_vec = Vector((0.0,0.0,0.0))

    # First the center is determined. All coordinates are summed up ...
    sum_vec = sum([atom.location for atom in all_atoms], sum_vec)

    # ... and the average is taken. This gives the center of the object.
    object_center_vec = sum_vec / Number_of_total_atoms

    # Now, we determine the size.The farthest atom from the object center is
    # taken as a measure. The size is used to place well the camera and light
    # into the scene.
    object_size_vec = [atom.location - object_center_vec for atom in all_atoms]
    object_size = max(object_size_vec).length

    # ------------------------------------------------------------------------
    # SORTING THE ATOMS

    # Lists of atoms of one type are created. Example:
    # draw_all_atoms = [ data_hydrogen,data_carbon,data_nitrogen ]
    # data_hydrogen = [["Hydrogen", Material_Hydrogen, Vector((x,y,z)), 109], ...]

    # Go through the list which contains all types of atoms. It is the list,
    # which has been created on the top during reading the PDB file.
    # Example: atom_all_types_list = ["hydrogen", "carbon", ...]
    draw_all_atoms = []
    for atom_type in atom_all_types_list:

        # Don't draw 'TER atoms'.
        if atom_type[0] == "TER":
            continue

        # This is the draw list, which contains all atoms of one type (e.g.
        # all hydrogens) ...
        draw_all_atoms_type = []

        # Go through all atoms ...
        for atom in all_atoms:
            # ... select the atoms of the considered type via comparison ...
            if atom.name == atom_type[0]:
                # ... and append them to the list 'draw_all_atoms_type'.
                draw_all_atoms_type.append([atom.name,
                                            atom.material,
                                            atom.location,
                                            atom.radius])

        # Now append the atom list to the list of all types of atoms
        draw_all_atoms.append(draw_all_atoms_type)

    # ------------------------------------------------------------------------
    # COLLECTION

    # Before we start to draw the atoms and sticks, we first create a
    # collection for the molecule. All atoms (balls) and sticks (cylinders)
    # are put into this collection.
    coll_molecule_name = os.path.basename(filepath_pdb)
    scene = bpy.context.scene
    coll_molecule = bpy.data.collections.new(coll_molecule_name)
    scene.collection.children.link(coll_molecule)

    # ------------------------------------------------------------------------
    # DRAWING THE ATOMS

    bpy.ops.object.select_all(action='DESELECT')

    list_coll_elements = []
    # For each list of atoms of ONE type (e.g. Hydrogen)
    for draw_all_atoms_type in draw_all_atoms:

        atom_mesh, coll_element = draw_atoms_one_type(draw_all_atoms_type,
                                                      Ball_type,
                                                      Ball_azimuth,
                                                      Ball_zenith,
                                                      Ball_radius_factor,
                                                      object_center_vec,
                                                      coll_molecule)
        atom_object_list.append(atom_mesh)
        list_coll_elements.append(coll_element)

    # ------------------------------------------------------------------------
    # DRAWING THE STICKS: cylinders in a dupliverts structure

    if use_sticks == True and use_sticks_type == '0' and all_sticks != []:

        sticks = draw_sticks_dupliverts(all_atoms,
                                        atom_all_types_list,
                                        object_center_vec,
                                        all_sticks,
                                        Stick_diameter,
                                        Stick_sectors,
                                        Stick_unit,
                                        Stick_dist,
                                        use_sticks_smooth,
                                        use_sticks_color,
                                        list_coll_elements)
        for stick in sticks:
            atom_object_list.append(stick)

    # ------------------------------------------------------------------------
    # DRAWING THE STICKS: skin and subdivision modifier

    if use_sticks == True and use_sticks_type == '1' and all_sticks != []:

        sticks = draw_sticks_skin(all_atoms,
                                  all_sticks,
                                  Stick_diameter,
                                  use_sticks_smooth,
                                  sticks_subdiv_view,
                                  sticks_subdiv_render,
                                  coll_molecule)
        atom_object_list.append(sticks)

    # ------------------------------------------------------------------------
    # DRAWING THE STICKS: normal cylinders

    if use_sticks == True and use_sticks_type == '2' and all_sticks != []:

        sticks = draw_sticks_normal(all_atoms,
                                    all_sticks,
                                    object_center_vec,
                                    Stick_diameter,
                                    Stick_sectors,
                                    Stick_dist,
                                    use_sticks_smooth,
                                    use_sticks_one_object,
                                    use_sticks_one_object_nr,
                                    coll_molecule)
        atom_object_list.append(sticks)

    # ------------------------------------------------------------------------
    # CAMERA and LIGHT SOURCES

    camera_light_source(use_camera,
                        use_light,
                        object_center_vec,
                        object_size)

    # ------------------------------------------------------------------------
    # SELECT ALL LOADED OBJECTS
    bpy.ops.object.select_all(action='DESELECT')
    obj = None
    for obj in atom_object_list:
        obj.select_set(True)

    # activate the last selected object
    if obj:
        bpy.context.view_layer.objects.active = obj
