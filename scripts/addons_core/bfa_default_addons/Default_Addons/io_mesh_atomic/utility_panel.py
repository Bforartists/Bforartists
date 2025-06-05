# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import bpy
import bmesh
from mathutils import Vector
from math import sqrt
from copy import copy

# -----------------------------------------------------------------------------
#                                                         Atom and element data


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
( 1,      "Hydrogen",        "H", (  1.0,   1.0,   1.0, 1.0), 0.32, 0.32, 0.79 , -1 , 1.54 ),
( 2,        "Helium",       "He", ( 0.85,   1.0,   1.0, 1.0), 0.93, 0.93, 0.49 ),
( 3,       "Lithium",       "Li", (  0.8,  0.50,   1.0, 1.0), 1.23, 1.23, 2.05 ,  1 , 0.68 ),
( 4,     "Beryllium",       "Be", ( 0.76,   1.0,   0.0, 1.0), 0.90, 0.90, 1.40 ,  1 , 0.44 ,  2 , 0.35 ),
( 5,         "Boron",        "B", (  1.0,  0.70,  0.70, 1.0), 0.82, 0.82, 1.17 ,  1 , 0.35 ,  3 , 0.23 ),
( 6,        "Carbon",        "C", ( 0.56,  0.56,  0.56, 1.0), 0.77, 0.77, 0.91 , -4 , 2.60 ,  4 , 0.16 ),
( 7,      "Nitrogen",        "N", ( 0.18,  0.31,  0.97, 1.0), 0.75, 0.75, 0.75 , -3 , 1.71 ,  1 , 0.25 ,  3 , 0.16 ,  5 , 0.13 ),
( 8,        "Oxygen",        "O", (  1.0,  0.05,  0.05, 1.0), 0.73, 0.73, 0.65 , -2 , 1.32 , -1 , 1.76 ,  1 , 0.22 ,  6 , 0.09 ),
( 9,      "Fluorine",        "F", ( 0.56,  0.87,  0.31, 1.0), 0.72, 0.72, 0.57 , -1 , 1.33 ,  7 , 0.08 ),
(10,          "Neon",       "Ne", ( 0.70,  0.89,  0.96, 1.0), 0.71, 0.71, 0.51 ,  1 , 1.12 ),
(11,        "Sodium",       "Na", ( 0.67,  0.36,  0.94, 1.0), 1.54, 1.54, 2.23 ,  1 , 0.97 ),
(12,     "Magnesium",       "Mg", ( 0.54,   1.0,   0.0, 1.0), 1.36, 1.36, 1.72 ,  1 , 0.82 ,  2 , 0.66 ),
(13,     "Aluminium",       "Al", ( 0.74,  0.65,  0.65, 1.0), 1.18, 1.18, 1.82 ,  3 , 0.51 ),
(14,       "Silicon",       "Si", ( 0.94,  0.78,  0.62, 1.0), 1.11, 1.11, 1.46 , -4 , 2.71 , -1 , 3.84 ,  1 , 0.65 ,  4 , 0.42 ),
(15,    "Phosphorus",        "P", (  1.0,  0.50,   0.0, 1.0), 1.06, 1.06, 1.23 , -3 , 2.12 ,  3 , 0.44 ,  5 , 0.35 ),
(16,        "Sulfur",        "S", (  1.0,   1.0,  0.18, 1.0), 1.02, 1.02, 1.09 , -2 , 1.84 ,  2 , 2.19 ,  4 , 0.37 ,  6 , 0.30 ),
(17,      "Chlorine",       "Cl", ( 0.12,  0.94,  0.12, 1.0), 0.99, 0.99, 0.97 , -1 , 1.81 ,  5 , 0.34 ,  7 , 0.27 ),
(18,         "Argon",       "Ar", ( 0.50,  0.81,  0.89, 1.0), 0.98, 0.98, 0.88 ,  1 , 1.54 ),
(19,     "Potassium",        "K", ( 0.56,  0.25,  0.83, 1.0), 2.03, 2.03, 2.77 ,  1 , 0.81 ),
(20,       "Calcium",       "Ca", ( 0.23,   1.0,   0.0, 1.0), 1.74, 1.74, 2.23 ,  1 , 1.18 ,  2 , 0.99 ),
(21,      "Scandium",       "Sc", ( 0.90,  0.90,  0.90, 1.0), 1.44, 1.44, 2.09 ,  3 , 0.73 ),
(22,      "Titanium",       "Ti", ( 0.74,  0.76,  0.78, 1.0), 1.32, 1.32, 2.00 ,  1 , 0.96 ,  2 , 0.94 ,  3 , 0.76 ,  4 , 0.68 ),
(23,      "Vanadium",        "V", ( 0.65,  0.65,  0.67, 1.0), 1.22, 1.22, 1.92 ,  2 , 0.88 ,  3 , 0.74 ,  4 , 0.63 ,  5 , 0.59 ),
(24,      "Chromium",       "Cr", ( 0.54,   0.6,  0.78, 1.0), 1.18, 1.18, 1.85 ,  1 , 0.81 ,  2 , 0.89 ,  3 , 0.63 ,  6 , 0.52 ),
(25,     "Manganese",       "Mn", ( 0.61,  0.47,  0.78, 1.0), 1.17, 1.17, 1.79 ,  2 , 0.80 ,  3 , 0.66 ,  4 , 0.60 ,  7 , 0.46 ),
(26,          "Iron",       "Fe", ( 0.87,   0.4,   0.2, 1.0), 1.17, 1.17, 1.72 ,  2 , 0.74 ,  3 , 0.64 ),
(27,        "Cobalt",       "Co", ( 0.94,  0.56,  0.62, 1.0), 1.16, 1.16, 1.67 ,  2 , 0.72 ,  3 , 0.63 ),
(28,        "Nickel",       "Ni", ( 0.31,  0.81,  0.31, 1.0), 1.15, 1.15, 1.62 ,  2 , 0.69 ),
(29,        "Copper",       "Cu", ( 0.78,  0.50,   0.2, 1.0), 1.17, 1.17, 1.57 ,  1 , 0.96 ,  2 , 0.72 ),
(30,          "Zinc",       "Zn", ( 0.49,  0.50,  0.69, 1.0), 1.25, 1.25, 1.53 ,  1 , 0.88 ,  2 , 0.74 ),
(31,       "Gallium",       "Ga", ( 0.76,  0.56,  0.56, 1.0), 1.26, 1.26, 1.81 ,  1 , 0.81 ,  3 , 0.62 ),
(32,     "Germanium",       "Ge", (  0.4,  0.56,  0.56, 1.0), 1.22, 1.22, 1.52 , -4 , 2.72 ,  2 , 0.73 ,  4 , 0.53 ),
(33,       "Arsenic",       "As", ( 0.74,  0.50,  0.89, 1.0), 1.20, 1.20, 1.33 , -3 , 2.22 ,  3 , 0.58 ,  5 , 0.46 ),
(34,      "Selenium",       "Se", (  1.0,  0.63,   0.0, 1.0), 1.16, 1.16, 1.22 , -2 , 1.91 , -1 , 2.32 ,  1 , 0.66 ,  4 , 0.50 ,  6 , 0.42 ),
(35,       "Bromine",       "Br", ( 0.65,  0.16,  0.16, 1.0), 1.14, 1.14, 1.12 , -1 , 1.96 ,  5 , 0.47 ,  7 , 0.39 ),
(36,       "Krypton",       "Kr", ( 0.36,  0.72,  0.81, 1.0), 1.31, 1.31, 1.24 ),
(37,      "Rubidium",       "Rb", ( 0.43,  0.18,  0.69, 1.0), 2.16, 2.16, 2.98 ,  1 , 1.47 ),
(38,     "Strontium",       "Sr", (  0.0,   1.0,   0.0, 1.0), 1.91, 1.91, 2.45 ,  2 , 1.12 ),
(39,       "Yttrium",        "Y", ( 0.58,   1.0,   1.0, 1.0), 1.62, 1.62, 2.27 ,  3 , 0.89 ),
(40,     "Zirconium",       "Zr", ( 0.58,  0.87,  0.87, 1.0), 1.45, 1.45, 2.16 ,  1 , 1.09 ,  4 , 0.79 ),
(41,       "Niobium",       "Nb", ( 0.45,  0.76,  0.78, 1.0), 1.34, 1.34, 2.08 ,  1 , 1.00 ,  4 , 0.74 ,  5 , 0.69 ),
(42,    "Molybdenum",       "Mo", ( 0.32,  0.70,  0.70, 1.0), 1.30, 1.30, 2.01 ,  1 , 0.93 ,  4 , 0.70 ,  6 , 0.62 ),
(43,    "Technetium",       "Tc", ( 0.23,  0.61,  0.61, 1.0), 1.27, 1.27, 1.95 ,  7 , 0.97 ),
(44,     "Ruthenium",       "Ru", ( 0.14,  0.56,  0.56, 1.0), 1.25, 1.25, 1.89 ,  4 , 0.67 ),
(45,       "Rhodium",       "Rh", ( 0.03,  0.49,  0.54, 1.0), 1.25, 1.25, 1.83 ,  3 , 0.68 ),
(46,     "Palladium",       "Pd", (  0.0,  0.41,  0.52, 1.0), 1.28, 1.28, 1.79 ,  2 , 0.80 ,  4 , 0.65 ),
(47,        "Silver",       "Ag", ( 0.75,  0.75,  0.75, 1.0), 1.34, 1.34, 1.75 ,  1 , 1.26 ,  2 , 0.89 ),
(48,       "Cadmium",       "Cd", (  1.0,  0.85,  0.56, 1.0), 1.48, 1.48, 1.71 ,  1 , 1.14 ,  2 , 0.97 ),
(49,        "Indium",       "In", ( 0.65,  0.45,  0.45, 1.0), 1.44, 1.44, 2.00 ,  3 , 0.81 ),
(50,           "Tin",       "Sn", (  0.4,  0.50,  0.50, 1.0), 1.41, 1.41, 1.72 , -4 , 2.94 , -1 , 3.70 ,  2 , 0.93 ,  4 , 0.71 ),
(51,      "Antimony",       "Sb", ( 0.61,  0.38,  0.70, 1.0), 1.40, 1.40, 1.53 , -3 , 2.45 ,  3 , 0.76 ,  5 , 0.62 ),
(52,     "Tellurium",       "Te", ( 0.83,  0.47,   0.0, 1.0), 1.36, 1.36, 1.42 , -2 , 2.11 , -1 , 2.50 ,  1 , 0.82 ,  4 , 0.70 ,  6 , 0.56 ),
(53,        "Iodine",        "I", ( 0.58,   0.0,  0.58, 1.0), 1.33, 1.33, 1.32 , -1 , 2.20 ,  5 , 0.62 ,  7 , 0.50 ),
(54,         "Xenon",       "Xe", ( 0.25,  0.61,  0.69, 1.0), 1.31, 1.31, 1.24 ),
(55,       "Caesium",       "Cs", ( 0.34,  0.09,  0.56, 1.0), 2.35, 2.35, 3.35 ,  1 , 1.67 ),
(56,        "Barium",       "Ba", (  0.0,  0.78,   0.0, 1.0), 1.98, 1.98, 2.78 ,  1 , 1.53 ,  2 , 1.34 ),
(57,     "Lanthanum",       "La", ( 0.43,  0.83,   1.0, 1.0), 1.69, 1.69, 2.74 ,  1 , 1.39 ,  3 , 1.06 ),
(58,        "Cerium",       "Ce", (  1.0,   1.0,  0.78, 1.0), 1.65, 1.65, 2.70 ,  1 , 1.27 ,  3 , 1.03 ,  4 , 0.92 ),
(59,  "Praseodymium",       "Pr", ( 0.85,   1.0,  0.78, 1.0), 1.65, 1.65, 2.67 ,  3 , 1.01 ,  4 , 0.90 ),
(60,     "Neodymium",       "Nd", ( 0.78,   1.0,  0.78, 1.0), 1.64, 1.64, 2.64 ,  3 , 0.99 ),
(61,    "Promethium",       "Pm", ( 0.63,   1.0,  0.78, 1.0), 1.63, 1.63, 2.62 ,  3 , 0.97 ),
(62,      "Samarium",       "Sm", ( 0.56,   1.0,  0.78, 1.0), 1.62, 1.62, 2.59 ,  3 , 0.96 ),
(63,      "Europium",       "Eu", ( 0.38,   1.0,  0.78, 1.0), 1.85, 1.85, 2.56 ,  2 , 1.09 ,  3 , 0.95 ),
(64,    "Gadolinium",       "Gd", ( 0.27,   1.0,  0.78, 1.0), 1.61, 1.61, 2.54 ,  3 , 0.93 ),
(65,       "Terbium",       "Tb", ( 0.18,   1.0,  0.78, 1.0), 1.59, 1.59, 2.51 ,  3 , 0.92 ,  4 , 0.84 ),
(66,    "Dysprosium",       "Dy", ( 0.12,   1.0,  0.78, 1.0), 1.59, 1.59, 2.49 ,  3 , 0.90 ),
(67,       "Holmium",       "Ho", (  0.0,   1.0,  0.61, 1.0), 1.58, 1.58, 2.47 ,  3 , 0.89 ),
(68,        "Erbium",       "Er", (  0.0,  0.90,  0.45, 1.0), 1.57, 1.57, 2.45 ,  3 , 0.88 ),
(69,       "Thulium",       "Tm", (  0.0,  0.83,  0.32, 1.0), 1.56, 1.56, 2.42 ,  3 , 0.87 ),
(70,     "Ytterbium",       "Yb", (  0.0,  0.74,  0.21, 1.0), 1.74, 1.74, 2.40 ,  2 , 0.93 ,  3 , 0.85 ),
(71,      "Lutetium",       "Lu", (  0.0,  0.67,  0.14, 1.0), 1.56, 1.56, 2.25 ,  3 , 0.85 ),
(72,       "Hafnium",       "Hf", ( 0.30,  0.76,   1.0, 1.0), 1.44, 1.44, 2.16 ,  4 , 0.78 ),
(73,      "Tantalum",       "Ta", ( 0.30,  0.65,   1.0, 1.0), 1.34, 1.34, 2.09 ,  5 , 0.68 ),
(74,      "Tungsten",        "W", ( 0.12,  0.58,  0.83, 1.0), 1.30, 1.30, 2.02 ,  4 , 0.70 ,  6 , 0.62 ),
(75,       "Rhenium",       "Re", ( 0.14,  0.49,  0.67, 1.0), 1.28, 1.28, 1.97 ,  4 , 0.72 ,  7 , 0.56 ),
(76,        "Osmium",       "Os", ( 0.14,   0.4,  0.58, 1.0), 1.26, 1.26, 1.92 ,  4 , 0.88 ,  6 , 0.69 ),
(77,       "Iridium",       "Ir", ( 0.09,  0.32,  0.52, 1.0), 1.27, 1.27, 1.87 ,  4 , 0.68 ),
(78,      "Platinum",       "Pt", ( 0.81,  0.81,  0.87, 1.0), 1.30, 1.30, 1.83 ,  2 , 0.80 ,  4 , 0.65 ),
(79,          "Gold",       "Au", (  1.0,  0.81,  0.13, 1.0), 1.34, 1.34, 1.79 ,  1 , 1.37 ,  3 , 0.85 ),
(80,       "Mercury",       "Hg", ( 0.72,  0.72,  0.81, 1.0), 1.49, 1.49, 1.76 ,  1 , 1.27 ,  2 , 1.10 ),
(81,      "Thallium",       "Tl", ( 0.65,  0.32,  0.30, 1.0), 1.48, 1.48, 2.08 ,  1 , 1.47 ,  3 , 0.95 ),
(82,          "Lead",       "Pb", ( 0.34,  0.34,  0.38, 1.0), 1.47, 1.47, 1.81 ,  2 , 1.20 ,  4 , 0.84 ),
(83,       "Bismuth",       "Bi", ( 0.61,  0.30,  0.70, 1.0), 1.46, 1.46, 1.63 ,  1 , 0.98 ,  3 , 0.96 ,  5 , 0.74 ),
(84,      "Polonium",       "Po", ( 0.67,  0.36,   0.0, 1.0), 1.46, 1.46, 1.53 ,  6 , 0.67 ),
(85,      "Astatine",       "At", ( 0.45,  0.30,  0.27, 1.0), 1.45, 1.45, 1.43 , -3 , 2.22 ,  3 , 0.85 ,  5 , 0.46 ),
(86,         "Radon",       "Rn", ( 0.25,  0.50,  0.58, 1.0), 1.00, 1.00, 1.34 ),
(87,      "Francium",       "Fr", ( 0.25,   0.0,   0.4, 1.0), 1.00, 1.00, 1.00 ,  1 , 1.80 ),
(88,        "Radium",       "Ra", (  0.0,  0.49,   0.0, 1.0), 1.00, 1.00, 1.00 ,  2 , 1.43 ),
(89,      "Actinium",       "Ac", ( 0.43,  0.67,  0.98, 1.0), 1.00, 1.00, 1.00 ,  3 , 1.18 ),
(90,       "Thorium",       "Th", (  0.0,  0.72,   1.0, 1.0), 1.65, 1.65, 1.00 ,  4 , 1.02 ),
(91,  "Protactinium",       "Pa", (  0.0,  0.63,   1.0, 1.0), 1.00, 1.00, 1.00 ,  3 , 1.13 ,  4 , 0.98 ,  5 , 0.89 ),
(92,       "Uranium",        "U", (  0.0,  0.56,   1.0, 1.0), 1.42, 1.42, 1.00 ,  4 , 0.97 ,  6 , 0.80 ),
(93,     "Neptunium",       "Np", (  0.0,  0.50,   1.0, 1.0), 1.00, 1.00, 1.00 ,  3 , 1.10 ,  4 , 0.95 ,  7 , 0.71 ),
(94,     "Plutonium",       "Pu", (  0.0,  0.41,   1.0, 1.0), 1.00, 1.00, 1.00 ,  3 , 1.08 ,  4 , 0.93 ),
(95,     "Americium",       "Am", ( 0.32,  0.36,  0.94, 1.0), 1.00, 1.00, 1.00 ,  3 , 1.07 ,  4 , 0.92 ),
(96,        "Curium",       "Cm", ( 0.47,  0.36,  0.89, 1.0), 1.00, 1.00, 1.00 ),
(97,     "Berkelium",       "Bk", ( 0.54,  0.30,  0.89, 1.0), 1.00, 1.00, 1.00 ),
(98,   "Californium",       "Cf", ( 0.63,  0.21,  0.83, 1.0), 1.00, 1.00, 1.00 ),
(99,   "Einsteinium",       "Es", ( 0.70,  0.12,  0.83, 1.0), 1.00, 1.00, 1.00 ),
(100,       "Fermium",       "Fm", ( 0.70,  0.12, 0.72, 1.0), 1.00, 1.00, 1.00 ),
(101,   "Mendelevium",       "Md", ( 0.70,  0.05, 0.65, 1.0), 1.00, 1.00, 1.00 ),
(102,      "Nobelium",       "No", ( 0.74,  0.05, 0.52, 1.0), 1.00, 1.00, 1.00 ),
(103,    "Lawrencium",       "Lr", ( 0.78,   0.0,  0.4, 1.0), 1.00, 1.00, 1.00 ),
(104,       "Vacancy",      "Vac", (  0.5,   0.5,  0.5, 1.0), 1.00, 1.00, 1.00),
(105,       "Default",  "Default", (  1.0,   1.0,  1.0, 1.0), 1.00, 1.00, 1.00),
(106,         "Stick",    "Stick", (  0.5,   0.5,  0.5, 1.0), 1.00, 1.00, 1.00),
)

# The list 'ELEMENTS' contains all data of the elements and will be used during
# runtime. The list will be initialized with the fixed
# data from above via the class below (ElementProp). One fixed list (above),
# which cannot be changed, and a list of classes with same data (ELEMENTS) exist.
# The list 'ELEMENTS' can be modified by e.g. loading a separate custom
# data file.
ELEMENTS = []


# This is the class, which stores the properties for one element.
class ElementProp(object):
    __slots__ = ('number',
                 'name',
                 'short_name',
                 'color',
                 'radii',
                 'radii_ionic',
                 'mat_P_BSDF',
                 'mat_Eevee')
    def __init__(self,
                 number,
                 name,
                 short_name,
                 color,
                 radii,
                 radii_ionic,
                 mat_P_BSDF,
                 mat_Eevee):
        self.number       = number
        self.name         = name
        self.short_name   = short_name
        self.color        = color
        self.radii        = radii
        self.radii_ionic  = radii_ionic
        self.mat_P_BSDF   = mat_P_BSDF
        self.mat_Eevee    = mat_Eevee


class PBSDFProp(object):
    __slots__ = ('Subsurface_method',
                 'Distribution',
                 'Subsurface_weight',
                 'Subsurface_radius',
                 'Metallic',
                 'Specular_ior_level',
                 'Specular_tint',
                 'Roughness',
                 'Anisotropic',
                 'Anisotropic_rotation',
                 'Sheen_weight',
                 'Sheen_tint',
                 'Coat_weight',
                 'Coat_roughness',
                 'IOR',
                 'Transmission_weight',
                 'Emission',
                 'Emission_strength',
                 'Alpha')
    def __init__(self,
                 Subsurface_method,
                 Distribution,
                 Subsurface_weight,
                 Subsurface_radius,
                 Metallic,
                 Specular_ior_level,
                 Specular_tint,
                 Roughness,
                 Anisotropic,
                 Anisotropic_rotation,
                 Sheen_weight,
                 Sheen_tint,
                 Coat_weight,
                 Coat_roughness,
                 IOR,
                 Transmission_weight,
                 Emission,
                 Emission_strength,
                 Alpha):
        self.Subsurface_method     = Subsurface_method
        self.Distribution          = Distribution
        self.Subsurface_weight     = Subsurface_weight
        self.Subsurface_radius     = Subsurface_radius
        self.Metallic              = Metallic
        self.Specular_ior_level    = Specular_ior_level
        self.Specular_tint         = Specular_tint
        self.Roughness             = Roughness
        self.Anisotropic           = Anisotropic
        self.Anisotropic_rotation  = Anisotropic_rotation
        self.Sheen_weight          = Sheen_weight
        self.Sheen_tint            = Sheen_tint
        self.Coat_weight           = Coat_weight
        self.Coat_roughness        = Coat_roughness
        self.IOR                   = IOR
        self.Transmission_weight   = Transmission_weight
        self.Emission              = Emission
        self.Emission_strength     = Emission_strength
        self.Alpha                 = Alpha


class EeveeProp(object):
    __slots__ = ('use_backface',
                 'blend_method',
                 'shadow_method',
                 'clip_threshold',
                 'use_screen_refraction',
                 'refraction_depth',
                 'use_sss_translucency',
                 'pass_index')
    def __init__(self,
                 use_backface,
                 blend_method,
                 shadow_method,
                 clip_threshold,
                 use_screen_refraction,
                 refraction_depth,
                 use_sss_translucency,
                 pass_index):
        self.use_backface          = use_backface
        self.blend_method          = blend_method
        self.shadow_method         = shadow_method
        self.clip_threshold        = clip_threshold
        self.use_screen_refraction = use_screen_refraction
        self.refraction_depth      = refraction_depth
        self.use_sss_translucency  = use_sss_translucency
        self.pass_index            = pass_index


# This function measures the distance between two selected objects.
def distance():

    # In the 'EDIT' mode
    if bpy.context.mode == 'EDIT_MESH':

        atom = bpy.context.edit_object
        bm = bmesh.from_edit_mesh(atom.data)
        locations = []

        for v in bm.verts:
            if v.select:
                locations.append(atom.matrix_world @ v.co)

        if len(locations) > 1:
            location1 = locations[0]
            location2 = locations[1]
        else:
            return "N.A"
    # In the 'OBJECT' mode
    else:

        if len(bpy.context.selected_objects) > 1:
            location1 = bpy.context.selected_objects[0].location
            location2 = bpy.context.selected_objects[1].location
        else:
            return "N.A."

    dv = location2 - location1
    dist = str(dv.length)
    pos = str.find(dist, ".")
    dist = dist[:pos+4]
    dist = dist + " A"

    return dist


def choose_objects(action_type,
                   radius_all,
                   radius_pm,
                   radius_type,
                   radius_type_ionic,
                   sticks_all):

    # Note all selected objects first.
    change_objects_all = []
    for atom in bpy.context.selected_objects:
        change_objects_all.append(atom)

    # This is very important now: If there are dupliverts structures, note
    # only the parents and NOT the children! Otherwise the double work is
    # done or the system can even crash if objects are deleted. - The
    # chidlren are accessed anyways (see below).
    change_objects = []
    for atom in change_objects_all:
        if atom.parent != None:
            FLAG = False
            for atom2 in change_objects:
                if atom2 == atom.parent:
                   FLAG = True
            if FLAG == False:
                change_objects.append(atom)
        else:
            change_objects.append(atom)

    # And now, consider all objects, which are in the list 'change_objects'.
    for atom in change_objects:
        if len(atom.children) != 0:
            for atom_child in atom.children:
                if atom_child.type in {'SURFACE', 'MESH', 'META'}:
                    modify_objects(action_type,
                                   atom_child,
                                   radius_all,
                                   radius_pm,
                                   radius_type,
                                   radius_type_ionic,
                                   sticks_all)
        else:
            if atom.type in {'SURFACE', 'MESH', 'META'}:
                modify_objects(action_type,
                               atom,
                               radius_all,
                               radius_pm,
                               radius_type,
                               radius_type_ionic,
                               sticks_all)


# Modifying the radius of a selected atom or stick
def modify_objects(action_type,
                   atom,
                   radius_all,
                   radius_pm,
                   radius_type,
                   radius_type_ionic,
                   sticks_all):

    # Modify atom radius (in pm)
    if action_type == "ATOM_RADIUS_PM" and "STICK" not in atom.name.upper():
        if radius_pm[0] in atom.name:
            atom.scale = (radius_pm[1]/100,) * 3

    # Modify atom radius (all selected)
    if action_type == "ATOM_RADIUS_ALL" and "STICK" not in atom.name.upper():
        atom.scale *= radius_all

    # Modify atom radius (type, van der Waals, atomic or ionic)
    if action_type == "ATOM_RADIUS_TYPE" and "STICK" not in atom.name.upper():
        for element in ELEMENTS:
            if element.name in atom.name:
                # For ionic radii
                if radius_type == '3':
                    charge_states = element.radii_ionic[::2]
                    charge_radii =  element.radii_ionic[1::2]
                    charge_state_chosen = int(radius_type_ionic) - 4

                    find = (lambda searchList, elem:
                            [[i for i, x in enumerate(searchList) if x == e]
                            for e in elem])
                    index = find(charge_states,[charge_state_chosen])[0]

                    # Is there a charge state?
                    if index != []:
                        atom.scale = (charge_radii[index[0]],) * 3

                # For atomic and van der Waals radii.
                else:
                    atom.scale = (element.radii[int(radius_type)],) * 3

    # Modify atom sticks
    if (action_type == "STICKS_RADIUS_ALL" and 'STICK' in atom.name.upper() and
                                    ('CUP'      in atom.name.upper() or
                                     'CYLINDER' in atom.name.upper())):

        # For dupliverts structures only: Make the cylinder or cup visible
        # first, otherwise one cannot go into EDIT mode. Note that 'atom' here
        # is in fact a 'stick' (cylinder or cup).
        # First, identify if it is a normal cylinder object or a dupliverts
        # structure. The identifier for a dupliverts structure is the parent's
        # name, which includes "_sticks_mesh"
        if "_sticks_mesh" in atom.parent.name:
            atom.hide_set(False)

        bpy.context.view_layer.objects.active = atom
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bm = bmesh.from_edit_mesh(atom.data)

        locations = []
        for v in bm.verts:
            locations.append(v.co)

        center = Vector((0.0,0.0,0.0))
        center = sum([location for location in locations], center)/len(locations)

        radius = sum([(loc[0]-center[0])**2+(loc[1]-center[1])**2
                     for loc in locations], 0)
        radius_new = radius * sticks_all

        for v in bm.verts:
            v.co[0] = ((v.co[0] - center[0]) / radius) * radius_new + center[0]
            v.co[1] = ((v.co[1] - center[1]) / radius) * radius_new + center[1]

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        # Hide again the representative stick (cylinder or cup) if it is a
        # dupliverts structure.
        if "_sticks_mesh" in atom.parent.name:
            atom.hide_set(True)

        bpy.context.view_layer.objects.active = None

    # Change the atom objects
    if action_type == "ATOM_REPLACE_OBJ" and "STICK" not in atom.name.upper():

        scn = bpy.context.scene.atom_blend

        material = atom.active_material
        new_material = draw_obj_material(scn.replace_objs_material, material)

        # Special object (like halo, etc.)
        if scn.replace_objs_special != '0':
            atom = draw_obj_special(scn.replace_objs_special, atom)
        # Standard geometrical objects
        else:
            # If the atom shape shall not be changed, then:
            if scn.replace_objs == '0':
                atom.active_material = new_material
            # If the atom shape shall change, then:
            else:
                atom = draw_obj(scn.replace_objs, atom, new_material)

        # Find the sticks, if present.
        sticks_cylinder, sticks_cup = find_sticks_of_atom(atom)

        # Dupliverts sticks
        if sticks_cylinder != None and sticks_cup != None:
            sticks_cylinder.active_material = new_material
            sticks_cup.active_material = new_material
        if sticks_cylinder != None and sticks_cup == None:
            # Normal sticks
            if type(sticks_cylinder) == list:
                for stick in sticks_cylinder:
                    stick.active_material = new_material
            # Skin sticks
            else:
                sticks_cylinder.active_material = new_material

        # If the atom is the representative ball of a dupliverts structure,
        # then make it invisible.
        if atom.parent != None:
            atom.hide_set(True)

    # Default shape and colors for atoms
    if action_type == "ATOM_DEFAULT_OBJ" and "STICK" not in atom.name.upper():

        scn = bpy.context.scene.atom_blend

        # We first obtain the element form the list of elements.
        for element in ELEMENTS:
            if element.name in atom.name:
                break

        # Create now a new material with normal properties. Note that the
        # 'normal material' initially used during the import could have been
        # deleted by the user. This is why we create a new one.
        if "vacancy" in atom.name.lower():
            new_material = draw_obj_material('2', atom.active_material)
        else:
            new_material = draw_obj_material('1', atom.active_material)
        # Assign now the correct color.
        mat_P_BSDF = next(n for n in new_material.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = element.color
        new_material.name = element.name + "_normal"

        # Create a new atom because the current atom might have any kind
        # of shape. For this, we use a definition from below since it also
        # deletes the old atom.
        if "vacancy" in atom.name.lower():
            new_atom = draw_obj('2', atom, new_material)
        else:
            new_atom = draw_obj('1b', atom, new_material)

        # Now assign the material properties, name and size.
        new_atom.active_material = new_material
        new_atom.name = element.name + "_ball"
        new_atom.scale = (element.radii[0],) * 3

        # Find the sticks, if present.
        sticks_cylinder, sticks_cup = find_sticks_of_atom(new_atom)

        # Dupliverts sticks
        if sticks_cylinder != None and sticks_cup != None:
            sticks_cylinder.active_material = new_material
            sticks_cup.active_material = new_material
        if sticks_cylinder != None and sticks_cup == None:
            # Normal sticks
            if type(sticks_cylinder) == list:
                for stick in sticks_cylinder:
                    stick.active_material = new_material
            # Skin sticks
            else:
                sticks_cylinder.active_material = new_material


# Separating atoms from a dupliverts structure.
def separate_atoms(scn):

    # Get the mesh.
    mesh = bpy.context.edit_object

    # Do nothing if it is not a dupliverts structure.
    if not mesh.instance_type == "VERTS":
       return {'FINISHED'}

    # This is the name of the mesh
    mesh_name = mesh.name
    # Get the collection
    coll = mesh.users_collection[0]

    # Get the coordinates of the selected vertices (atoms)
    bm = bmesh.from_edit_mesh(mesh.data)
    locations = []
    for v in bm.verts:
        if v.select:
            locations.append(mesh.matrix_world @ v.co)

    # Free memory
    bm.free()

    # Delete already the selected vertices
    bpy.ops.mesh.delete(type='VERT')

    # Find the representative ball within the collection.
    for obj in coll.objects:
        if obj.parent != None:
            if obj.parent.name == mesh_name:
                break

    # Create balls and put them at the places where the vertices (atoms) have
    # been before.
    for location in locations:
        obj_dupli = obj.copy()
        obj_dupli.data = obj.data.copy()
        obj_dupli.parent = None
        coll.objects.link(obj_dupli)
        obj_dupli.location = location
        obj_dupli.name = obj.name + "_sep"
        # Do not hide the object!
        obj_dupli.hide_set(False)

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.context.view_layer.objects.active = mesh


# Prepare a new material
def draw_obj_material(material_type, material):

    mat_P_BSDF_default = next(n for n in material.node_tree.nodes
                              if n.type == "BSDF_PRINCIPLED")
    default_color = mat_P_BSDF_default.inputs['Base Color'].default_value

    if material_type == '0': # Unchanged
        material_new = material
    if material_type == '1': # Normal
        # We create again the 'normal' material. Why? It's because the old
        # one could have been deleted by the user during the course of the
        # user's work in Blender ... .
        material_new = bpy.data.materials.new(material.name + "_normal")
        material_new.use_nodes = True
        mat_P_BSDF = next(n for n in material_new.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = default_color
        mat_P_BSDF.inputs['Metallic'].default_value = 0.0
        mat_P_BSDF.inputs['Specular IOR Level'].default_value = 0.5
        mat_P_BSDF.inputs['Roughness'].default_value = 0.5
        mat_P_BSDF.inputs['Coat Roughness'].default_value = 0.03
        mat_P_BSDF.inputs['IOR'].default_value = 1.45
        mat_P_BSDF.inputs['Transmission Weight'].default_value = 0.0
        mat_P_BSDF.inputs['Alpha'].default_value = 1.0
        # Some additional stuff for eevee.
        material_new.blend_method = 'OPAQUE'
        material_new.shadow_method = 'OPAQUE'
    if material_type == '2': # Transparent
        material_new = bpy.data.materials.new(material.name + "_transparent")
        material_new.use_nodes = True
        mat_P_BSDF = next(n for n in material_new.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = default_color
        mat_P_BSDF.inputs['Metallic'].default_value = 0.0
        mat_P_BSDF.inputs['Specular IOR Level'].default_value = 0.15
        mat_P_BSDF.inputs['Roughness'].default_value = 0.2
        mat_P_BSDF.inputs['Coat Roughness'].default_value = 0.37
        mat_P_BSDF.inputs['IOR'].default_value = 1.45
        mat_P_BSDF.inputs['Transmission Weight'].default_value = 0.8
        mat_P_BSDF.inputs['Alpha'].default_value = 0.4
        # Some additional stuff for eevee.
        material_new.blend_method = 'HASHED'
        material_new.shadow_method = 'HASHED'
        material_new.use_backface_culling = False
    if material_type == '3': # Reflecting
        material_new = bpy.data.materials.new(material.name + "_reflecting")
        material_new.use_nodes = True
        mat_P_BSDF = next(n for n in material_new.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = default_color
        mat_P_BSDF.inputs['Metallic'].default_value = 0.7
        mat_P_BSDF.inputs['Specular IOR Level'].default_value = 0.15
        mat_P_BSDF.inputs['Roughness'].default_value = 0.1
        mat_P_BSDF.inputs['Coat Roughness'].default_value = 0.5
        mat_P_BSDF.inputs['IOR'].default_value = 0.8
        mat_P_BSDF.inputs['Transmission Weight'].default_value = 0.0
        mat_P_BSDF.inputs['Alpha'].default_value = 1.0
        # Some additional stuff for eevee.
        material_new.blend_method = 'OPAQUE'
        material_new.shadow_method = 'OPAQUE'
    if material_type == '4': # Transparent + reflecting
        material_new = bpy.data.materials.new(material.name + "_trans+refl")
        material_new.use_nodes = True
        mat_P_BSDF = next(n for n in material_new.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = default_color
        mat_P_BSDF.inputs['Metallic'].default_value = 0.5
        mat_P_BSDF.inputs['Specular IOR Level'].default_value = 0.15
        mat_P_BSDF.inputs['Roughness'].default_value = 0.05
        mat_P_BSDF.inputs['Coat Roughness'].default_value = 0.37
        mat_P_BSDF.inputs['IOR'].default_value = 1.45
        mat_P_BSDF.inputs['Transmission Weight'].default_value = 0.6
        mat_P_BSDF.inputs['Alpha'].default_value = 0.6
        # Some additional stuff for eevee.
        material_new.blend_method = 'HASHED'
        material_new.shadow_method = 'HASHED'
        material_new.use_backface_culling = False

    # Always, when the material is changed, a new name is created. Note that
    # this makes sense: Imagine, an other object uses the same material as the
    # selected one. After changing the material of the selected object the old
    # material should certainly not change and remain the same.
    if material_type in {'1','2','3','4'}:
        if "_repl" in material.name:
            pos = material.name.rfind("_repl")
            if material.name[pos+5:].isdigit():
                counter = int(material.name[pos+5:])
                material_new.name = material.name[:pos]+"_repl"+str(counter+1)
            else:
                material_new.name = material.name+"_repl1"
        else:
            material_new.name = material.name+"_repl1"
        material_new.diffuse_color = material.diffuse_color

    return material_new


# Get the collection of an object.
def get_collection_object(obj):

    coll_all = obj.users_collection
    if len(coll_all) > 0:
        coll = coll_all[0]
    else:
        coll = bpy.context.scene.collection

    return coll


# Find the sticks of an atom.
def find_sticks_of_atom(atom):

    # Initialization of the stick objects 'cylinder' and 'cup'.
    sticks_cylinder = None
    sticks_cup = None

    # This is for dupliverts structures.
    if atom.parent != None:

        D = bpy.data
        C = bpy.context

        # Get a list of all scenes.
        cols_scene = [c for c in D.collections if C.scene.user_of_id(c)]

        # This is the collection where the atom is inside.
        col_atom = atom.parent.users_collection[0]

        # Get the parent collection of the latter collection.
        col_parent = [c for c in cols_scene if c.user_of_id(col_atom)][0]

        # Get **all** children collections inside this parent collection.
        parent_childrens = col_parent.children_recursive

        # This is for dupliverts stick structures now: for each child
        # collection do:
        for child in parent_childrens:
            # It should not have the name of the atom collection.
            if child.name != col_atom.name:
                # If the sticks are inside then ...
                if "sticks" in child.name:
                    # For all objects do ...
                    for obj in child.objects:
                        # If the stick objects are inside then note them.
                        if "sticks_cylinder" in obj.name:
                            sticks_cylinder = obj
                        if "sticks_cup" in obj.name:
                            sticks_cup = obj

        # No dupliverts stick structures found? Then lets search for
        # 'normal' and 'skin' sticks. Such sticks are in the collection
        # 'Sticks' of the atomic structure.
        if sticks_cylinder == None and sticks_cup == None:

            # Get the grandparent collection of the parent collection.
            col_grandparent = [c for c in cols_scene if c.user_of_id(col_parent)][0]

            # Skin sticks:
            list_objs = col_grandparent.objects
            for obj in list_objs:
                if "Sticks" in obj.name:
                    sticks_cylinder = obj
                    break

            # Normal sticks
            if sticks_cylinder == None:
                # For each child collection do:
                for child in col_grandparent.children_recursive:
                    # If the sticks are inside then ...
                    if "Sticks_cylinders" in child.name:
                        sticks_cylinder = []
                        for obj in child.objects:
                            sticks_cylinder.append(obj)
                        break

    # Return the stick objects 'cylinder' and 'cup'.
    #
    # Dupliverts sticks => sticks_cylinder = 1,   sticks_cup = 1
    # Skin sticks       => sticks_cylinder = 1,   sticks_cup = None
    # Normal sticks     => sticks_cylinder = [n], sticks_cup = None
    return sticks_cylinder, sticks_cup


# Draw an object (e.g. cube, sphere, cylinder, ...)
def draw_obj(atom_shape, atom, new_material):

    # No change
    if atom_shape == '0':
        return None

    if atom_shape == '1a': #Sphere mesh
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=32,
            ring_count=32,
            radius=1,
            align='WORLD',
            enter_editmode=False,
            location=atom.location,
            rotation=(0, 0, 0))
    if atom_shape == '1b': #Sphere NURBS
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(
            align='WORLD',
            enter_editmode=False,
            location=atom.location,
            rotation=(0.0, 0.0, 0.0))
    if atom_shape == '2': #Cube
        bpy.ops.mesh.primitive_cube_add(
            align='WORLD',
            enter_editmode=False,
            location=atom.location,
            rotation=(0.0, 0.0, 0.0))
    if atom_shape == '3': #Plane
        bpy.ops.mesh.primitive_plane_add(
            align='WORLD',
            enter_editmode=False,
            location=atom.location,
            rotation=(0.0, 0.0, 0.0))
    if atom_shape == '4a': #Circle
        bpy.ops.mesh.primitive_circle_add(
            vertices=32,
            radius=1,
            fill_type='NOTHING',
            align='WORLD',
            enter_editmode=False,
            location=atom.location,
            rotation=(0, 0, 0))
    if atom_shape == '4b': #Circle NURBS
        bpy.ops.surface.primitive_nurbs_surface_circle_add(
            align='WORLD',
            enter_editmode=False,
            location=atom.location,
            rotation=(0, 0, 0))
    if atom_shape in {'5a','5b','5c','5d','5e'}: #Icosphere
        index = {'5a':1,'5b':2,'5c':3,'5d':4,'5e':5}
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=int(index[atom_shape]),
            radius=1,
            align='WORLD',
            enter_editmode=False,
            location=atom.location,
            rotation=(0, 0, 0))
    if atom_shape == '6a': #Cylinder
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=32,
            radius=1,
            depth=2,
            end_fill_type='NGON',
            align='WORLD',
            enter_editmode=False,
            location=atom.location,
            rotation=(0, 0, 0))
    if atom_shape == '6b': #Cylinder NURBS
        bpy.ops.surface.primitive_nurbs_surface_cylinder_add(
            align='WORLD',
            enter_editmode=False,
            location=atom.location,
            rotation=(0, 0, 0))
    if atom_shape == '7': #Cone
        bpy.ops.mesh.primitive_cone_add(
            vertices=32,
            radius1=1,
            radius2=0,
            depth=2,
            end_fill_type='NGON',
            align='WORLD',
            enter_editmode=False,
            location=atom.location,
            rotation=(0, 0, 0))
    if atom_shape == '8a': #Torus
        bpy.ops.mesh.primitive_torus_add(
            rotation=(0, 0, 0),
            location=atom.location,
            align='WORLD',
            major_radius=1,
            minor_radius=0.25,
            major_segments=48,
            minor_segments=12,
            abso_major_rad=1,
            abso_minor_rad=0.5)
    if atom_shape == '8b': #Torus NURBS
        bpy.ops.surface.primitive_nurbs_surface_torus_add(
            align='WORLD',
            enter_editmode=False,
            location=atom.location,
            rotation=(0, 0, 0))

    new_atom = bpy.context.view_layer.objects.active
    new_atom.scale = atom.scale + Vector((0.0,0.0,0.0))
    new_atom.name = atom.name
    new_atom.select_set(True)

    new_atom.active_material = new_material

    # If it is the representative object of a duplivert structure then
    # transfer the parent and hide the new object.
    if atom.parent != None:
        new_atom.parent = atom.parent
        new_atom.hide_set(True)

    # Note the collection where the old object was placed into.
    coll_old_atom = get_collection_object(atom)

    # Note the collection where the new object was placed into.
    coll_new_atom_past = get_collection_object(new_atom)

    # If it is not the same collection then ...
    if coll_new_atom_past != coll_old_atom:
        # Put the new object into the collection of the old object and ...
        coll_old_atom.objects.link(new_atom)
        # ... unlink the new atom from its original collection.
        coll_new_atom_past.objects.unlink(new_atom)

    # If necessary, remove the childrens of the old object.
    for child in atom.children:
        bpy.ops.object.select_all(action='DESELECT')
        child.hide_set(True)
        child.select_set(True)
        child.parent = None
        coll_child = get_collection_object(child)
        coll_child.objects.unlink(child)
        bpy.ops.object.delete()

    # Deselect everything
    bpy.ops.object.select_all(action='DESELECT')
    # Make the old atom visible.
    atom.hide_set(True)
    # Select the old atom.
    atom.select_set(True)
    # Remove the parent if necessary.
    atom.parent = None
    # Unlink the old object from the collection.
    coll_old_atom.objects.unlink(atom)
    # Delete the old atom
    bpy.ops.object.delete()

    #if "_F2+_center" or "_F+_center" or "_F0_center" in coll_old_atom:
    #    print("Delete the collection")

    return new_atom


# Draw a special object (e.g. halo, etc. ...)
def draw_obj_special(atom_shape, atom):

    # Note the collection where 'atom' is placed into.
    coll_atom = get_collection_object(atom)

    # Now, create a collection for the new objects
    coll_new = atom.name
    # Create the new collection and ...
    coll_new = bpy.data.collections.new(coll_new)
    # ... link it to the collection, which contains 'atom'.
    coll_atom.children.link(coll_new)

    # Get the color of the selected atom.
    material = atom.active_material
    mat_P_BSDF_default = next(n for n in material.node_tree.nodes
                      if n.type == "BSDF_PRINCIPLED")
    default_color = mat_P_BSDF_default.inputs['Base Color'].default_value

    # Create first a cube
    bpy.ops.mesh.primitive_cube_add(align='WORLD',
                                    enter_editmode=False,
                                    location=atom.location,
                                    rotation=(0.0, 0.0, 0.0))
    cube = bpy.context.view_layer.objects.active
    cube.scale = atom.scale + Vector((0.0,0.0,0.0))
    cube.select_set(True)

    # F2+ center
    if atom_shape == '1':
        cube.name = atom.name + "_F2+_vac"

        # New material for this cube
        material_new = bpy.data.materials.new(atom.name + "_F2+_vac")
        material_new.use_nodes = True
        mat_P_BSDF = next(n for n in material_new.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = default_color
        mat_P_BSDF.inputs['Metallic'].default_value = 0.7
        mat_P_BSDF.inputs['Specular IOR Level'].default_value = 0.0
        mat_P_BSDF.inputs['Roughness'].default_value = 0.65
        mat_P_BSDF.inputs['Coat Roughness'].default_value = 0.0
        mat_P_BSDF.inputs['IOR'].default_value = 1.45
        mat_P_BSDF.inputs['Transmission Weight'].default_value = 0.6
        mat_P_BSDF.inputs['Alpha'].default_value = 0.6
        # Some additional stuff for eevee.
        material_new.blend_method = 'HASHED'
        material_new.shadow_method = 'HASHED'
        material_new.use_backface_culling = False
        cube.active_material = material_new

        # Put a point lamp inside the defect.
        lamp_data = bpy.data.lights.new(name=atom.name + "_F2+_lamp", type="POINT")
        lamp_data.distance = atom.scale[0] * 2.0
        lamp_data.energy = 2000.0
        lamp_data.color = (0.8, 0.8, 0.8)
        lamp = bpy.data.objects.new(atom.name + "_F2+_lamp", lamp_data)
        lamp.location = Vector((0.0, 0.0, 0.0))
        bpy.context.collection.objects.link(lamp)
        lamp.parent = cube

        # The new 'atom' is the F2+ defect
        new_atom = cube

        # Note the collection where all the new objects were placed into.
        # We use only one object, the cube
        coll_ori = get_collection_object(cube)

        # If it is not the same collection then ...
        if coll_ori != coll_new:
            # Put all new objects into the new collection and ...
            coll_new.objects.link(cube)
            coll_new.objects.link(lamp)
            # ... unlink them from their original collection.
            coll_ori.objects.unlink(cube)
            coll_ori.objects.unlink(lamp)

        coll_new.name = atom.name + "_F2+_center"

        if atom.parent != None:
            cube.parent = atom.parent
            cube.hide_set(True)
            lamp.hide_set(True)

    # F+ center
    if atom_shape == '2':
        cube.name = atom.name + "_F2+_vac"

        # New material for this cube
        material_new = bpy.data.materials.new(atom.name + "_F2+_vac")
        material_new.use_nodes = True
        mat_P_BSDF = next(n for n in material_new.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = [0.0, 0.0, 0.8, 1.0]
        mat_P_BSDF.inputs['Metallic'].default_value = 0.7
        mat_P_BSDF.inputs['Specular IOR Level'].default_value = 0.0
        mat_P_BSDF.inputs['Roughness'].default_value = 0.65
        mat_P_BSDF.inputs['Coat Roughness'].default_value = 0.0
        mat_P_BSDF.inputs['IOR'].default_value = 1.45
        mat_P_BSDF.inputs['Transmission Weight'].default_value = 0.6
        mat_P_BSDF.inputs['Alpha'].default_value = 0.6
        # Some additional stuff for eevee.
        material_new.blend_method = 'HASHED'
        material_new.shadow_method = 'HASHED'
        material_new.use_backface_culling = False
        cube.active_material = material_new

        # Create now an electron
        scale = atom.scale / 10.0
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                                        align='WORLD',
                                        enter_editmode=False,
                                        location=(0.0, 0.0, 0.0),
                                        rotation=(0.0, 0.0, 0.0))
        electron = bpy.context.view_layer.objects.active
        electron.scale = scale
        electron.name = atom.name + "_F+_electron"
        electron.parent = cube
        # New material for the electron
        material_electron = bpy.data.materials.new(atom.name + "_F+-center")
        material_electron.use_nodes = True
        mat_P_BSDF = next(n for n in material_electron.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = [0.0, 0.0, 0.8, 1.0]
        mat_P_BSDF.inputs['Metallic'].default_value = 0.8
        mat_P_BSDF.inputs['Specular IOR Level'].default_value = 0.0
        mat_P_BSDF.inputs['Roughness'].default_value = 0.3
        mat_P_BSDF.inputs['Coat Roughness'].default_value = 0.0
        mat_P_BSDF.inputs['IOR'].default_value = 1.45
        mat_P_BSDF.inputs['Transmission Weight'].default_value = 0.6
        mat_P_BSDF.inputs['Alpha'].default_value = 1.0
        # Some additional stuff for eevee.
        material_electron.blend_method = 'OPAQUE'
        material_electron.shadow_method = 'OPAQUE'
        material_electron.use_backface_culling = False
        electron.active_material = material_electron

        # Put a point lamp inside the electron
        lamp_data = bpy.data.lights.new(name=atom.name + "_F+_lamp", type="POINT")
        lamp_data.distance = atom.scale[0] * 2.0
        lamp_data.energy = 100000.0
        lamp_data.color = (0.0, 0.0, 0.8)
        lamp = bpy.data.objects.new(atom.name + "_F+_lamp", lamp_data)
        lamp.location = Vector((scale[0]*1.5, 0.0, 0.0))
        bpy.context.collection.objects.link(lamp)
        lamp.parent = cube

        # The new 'atom' is the F+ defect complex + lamp
        new_atom = cube

        # Note the collection where all the new objects were placed into.
        # We use only one object, the cube
        coll_ori = get_collection_object(cube)

        # If it is not the same collection then ...
        if coll_ori != coll_new:
            # Put all new objects into the new collection and ...
            coll_new.objects.link(cube)
            coll_new.objects.link(electron)
            coll_new.objects.link(lamp)
            # ... unlink them from their original collection.
            coll_ori.objects.unlink(cube)
            coll_ori.objects.unlink(electron)
            coll_ori.objects.unlink(lamp)

        coll_new.name = atom.name + "_F+_center"

        if atom.parent != None:
            cube.parent = atom.parent
            cube.hide_set(True)
            electron.hide_set(True)
            lamp.hide_set(True)

    # F0 center
    if atom_shape == '3':
        cube.name = atom.name + "_F2+_vac"

        # New material for this cube
        material_new = bpy.data.materials.new(atom.name + "_F2+_vac")
        material_new.use_nodes = True
        mat_P_BSDF = next(n for n in material_new.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = [0.8, 0.0, 0.0, 1.0]
        mat_P_BSDF.inputs['Metallic'].default_value = 0.7
        mat_P_BSDF.inputs['Specular IOR Level'].default_value = 0.0
        mat_P_BSDF.inputs['Roughness'].default_value = 0.65
        mat_P_BSDF.inputs['Coat Roughness'].default_value = 0.0
        mat_P_BSDF.inputs['IOR'].default_value = 1.45
        mat_P_BSDF.inputs['Transmission Weight'].default_value = 0.6
        mat_P_BSDF.inputs['Alpha'].default_value = 0.6
        # Some additional stuff for eevee.
        material_new.blend_method = 'HASHED'
        material_new.shadow_method = 'HASHED'
        material_new.use_backface_culling = False
        cube.active_material = material_new

        # Create now two electrons ... .
        scale = atom.scale / 10.0
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                                        align='WORLD',
                                        enter_editmode=False,
                                        location=(scale[0]*1.5,0.0,0.0),
                                        rotation=(0.0, 0.0, 0.0))
        electron1 = bpy.context.view_layer.objects.active
        electron1.scale = scale
        electron1.name = atom.name + "_F0_electron_1"
        electron1.parent = cube
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                                        align='WORLD',
                                        enter_editmode=False,
                                        location=(-scale[0]*1.5,0.0,0.0),
                                        rotation=(0.0, 0.0, 0.0))
        electron2 = bpy.context.view_layer.objects.active
        electron2.scale = scale
        electron2.name = atom.name + "_F0_electron_2"
        electron2.parent = cube
        # Create a new material for the two electrons.
        material_electron = bpy.data.materials.new(atom.name + "_F0-center")
        material_electron.use_nodes = True
        mat_P_BSDF = next(n for n in material_electron.node_tree.nodes
                          if n.type == "BSDF_PRINCIPLED")
        mat_P_BSDF.inputs['Base Color'].default_value = [0.0, 0.0, 0.8, 1.0]
        mat_P_BSDF.inputs['Metallic'].default_value = 0.8
        mat_P_BSDF.inputs['Specular IOR Level'].default_value = 0.0
        mat_P_BSDF.inputs['Roughness'].default_value = 0.3
        mat_P_BSDF.inputs['Coat Roughness'].default_value = 0.0
        mat_P_BSDF.inputs['IOR'].default_value = 1.45
        mat_P_BSDF.inputs['Transmission Weight'].default_value = 0.6
        mat_P_BSDF.inputs['Alpha'].default_value = 1.0
        # Some additional stuff for eevee.
        material_electron.blend_method = 'OPAQUE'
        material_electron.shadow_method = 'OPAQUE'
        material_electron.use_backface_culling = False
        # We assign the materials to the two electrons.
        electron1.active_material = material_electron
        electron2.active_material = material_electron

        # Put two point lamps inside the electrons.
        lamp1_data = bpy.data.lights.new(name=atom.name + "_F0_lamp_1", type="POINT")
        lamp1_data.distance = atom.scale[0] * 2.0
        lamp1_data.energy = 20000.0
        lamp1_data.color = (0.8, 0.0, 0.0)
        lamp1 = bpy.data.objects.new(atom.name + "_F0_lamp", lamp1_data)
        lamp1.location = Vector((scale[0]*1.5, 0.0, 0.0))
        bpy.context.collection.objects.link(lamp1)
        lamp1.parent = cube
        lamp2_data = bpy.data.lights.new(name=atom.name + "_F0_lamp_2", type="POINT")
        lamp2_data.distance = atom.scale[0] * 2.0
        lamp2_data.energy = 20000.0
        lamp2_data.color = (0.8, 0.0, 0.0)
        lamp2 = bpy.data.objects.new(atom.name + "_F0_lamp", lamp2_data)
        lamp2.location = Vector((-scale[0]*1.5, 0.0, 0.0))
        bpy.context.collection.objects.link(lamp2)
        lamp2.parent = cube

        # The new 'atom' is the F0 defect complex + lamps
        new_atom = cube

        # Note the collection where all the new objects were placed into.
        # We use only one object, the cube
        coll_ori = get_collection_object(cube)

        # If it is not the same collection then ...
        if coll_ori != coll_new:
            # Put all new objects into the collection of 'atom' and ...
            coll_new.objects.link(cube)
            coll_new.objects.link(electron1)
            coll_new.objects.link(electron2)
            coll_new.objects.link(lamp1)
            coll_new.objects.link(lamp2)
            # ... unlink them from their original collection.
            coll_ori.objects.unlink(cube)
            coll_ori.objects.unlink(electron1)
            coll_ori.objects.unlink(electron2)
            coll_ori.objects.unlink(lamp1)
            coll_ori.objects.unlink(lamp2)

        coll_new.name = atom.name + "_F0_center"

        if atom.parent != None:
            cube.parent = atom.parent
            cube.hide_set(True)
            electron1.hide_set(True)
            electron2.hide_set(True)
            lamp1.hide_set(True)
            lamp2.hide_set(True)

    # Deselect everything
    bpy.ops.object.select_all(action='DESELECT')
    # Make the old atom visible.
    atom.hide_set(True)
    # Select the old atom.
    atom.select_set(True)
    # Remove the parent if necessary.
    atom.parent = None
    # Unlink the old object from the collection.
    coll_atom.objects.unlink(atom)
    # Delete the old atom
    bpy.ops.object.delete()

    return new_atom


# Initialization of the list 'ELEMENTS'.
def read_elements():

    del ELEMENTS[:]

    for item in ELEMENTS_DEFAULT:

        # All three radii into a list
        radii = [item[4],item[5],item[6]]
        # The handling of the ionic radii will be done later. So far, it is an
        # empty list.
        radii_ionic = item[7:]

        li = ElementProp(item[0], item[1], item[2], item[3], radii, radii_ionic, [], [])

        ELEMENTS.append(li)


# Custom data file: changing color and radii by using the list 'ELEMENTS'.
def custom_datafile_change_atom_props():

    for atom in bpy.context.selected_objects:

        FLAG = False
        if len(atom.children) != 0:
            child = atom.children[0]
            if child.type in {'SURFACE', 'MESH', 'META'}:
                for element in ELEMENTS:
                    if element.name in atom.name:
                        obj = child
                        e = element
                        FLAG = True
        else:
            if atom.type in {'SURFACE', 'MESH', 'META'}:
                for element in ELEMENTS:
                    if element.name in atom.name:
                        obj = atom
                        e = element
                        FLAG = True

        if FLAG:
            obj.scale = (e.radii[0],) * 3
            mat = obj.active_material
            mat_P_BSDF = next(n for n in mat.node_tree.nodes
                              if n.type == "BSDF_PRINCIPLED")

            mat_P_BSDF.inputs['Base Color'].default_value = e.color
            mat_P_BSDF.subsurface_method = e.mat_P_BSDF.Subsurface_method
            mat_P_BSDF.distribution = e.mat_P_BSDF.Distribution
            mat_P_BSDF.inputs['Subsurface Weight'].default_value = e.mat_P_BSDF.Subsurface_weight
            mat_P_BSDF.inputs['Subsurface Radius'].default_value = e.mat_P_BSDF.Subsurface_radius
            mat_P_BSDF.inputs['Metallic'].default_value = e.mat_P_BSDF.Metallic
            mat_P_BSDF.inputs['Specular IOR Level'].default_value = e.mat_P_BSDF.Specular_ior_level
            mat_P_BSDF.inputs['Specular Tint'].default_value = e.mat_P_BSDF.Specular_tint
            mat_P_BSDF.inputs['Roughness'].default_value = e.mat_P_BSDF.Roughness
            mat_P_BSDF.inputs['Anisotropic'].default_value = e.mat_P_BSDF.Anisotropic
            mat_P_BSDF.inputs['Anisotropic Rotation'].default_value = e.mat_P_BSDF.Anisotropic_rotation
            mat_P_BSDF.inputs['Sheen Weight'].default_value = e.mat_P_BSDF.Sheen_weight
            mat_P_BSDF.inputs['Sheen Tint'].default_value = e.mat_P_BSDF.Sheen_tint
            mat_P_BSDF.inputs['Coat Weight'].default_value = e.mat_P_BSDF.Coat_weight
            mat_P_BSDF.inputs['Coat Roughness'].default_value = e.mat_P_BSDF.Coat_roughness
            mat_P_BSDF.inputs['IOR'].default_value = e.mat_P_BSDF.IOR
            mat_P_BSDF.inputs['Transmission Weight'].default_value = e.mat_P_BSDF.Transmission_weight
            mat_P_BSDF.inputs['Emission'].default_value = e.mat_P_BSDF.Emission
            mat_P_BSDF.inputs['Emission Strength'].default_value = e.mat_P_BSDF.Emission_strength
            mat_P_BSDF.inputs['Alpha'].default_value = e.mat_P_BSDF.Alpha

            mat.use_backface_culling = e.mat_Eevee.use_backface
            mat.blend_method = e.mat_Eevee.blend_method
            mat.shadow_method = e.mat_Eevee.shadow_method
            mat.alpha_threshold = e.mat_Eevee.clip_threshold
            mat.use_screen_refraction = e.mat_Eevee.use_screen_refraction
            mat.refraction_depth = e.mat_Eevee.refraction_depth
            mat.use_sss_translucency = e.mat_Eevee.use_sss_translucency
            mat.pass_index = e.mat_Eevee.pass_index

            FLAG = False

    bpy.ops.object.select_all(action='DESELECT')


# Reading a custom data file and modifying the list 'ELEMENTS'.
def custom_datafile(path_datafile):

    if path_datafile == "":
        return False

    path_datafile = bpy.path.abspath(path_datafile)

    if os.path.isfile(path_datafile) == False:
        return False

    # The whole list gets deleted! We build it new.
    del ELEMENTS[:]

    # Read the data file, which contains all data
    # (atom name, radii, colors, etc.)
    data_file_p = open(path_datafile, "r")

    for line in data_file_p:

        if "#" == line[0]:
            continue

        if "Atom" in line:

            list_radii_ionic = []
            while True:

                if len(line) in [0,1]:
                    break

                # Number
                if "Number                       :" in line:
                    pos = line.rfind(':') + 1
                    number = line[pos:].strip()
                # Name
                if "Name                         :" in line:
                    pos = line.rfind(':') + 1
                    name = line[pos:].strip()
                # Short name
                if "Short name                   :" in line:
                    pos = line.rfind(':') + 1
                    short_name = line[pos:].strip()
                # Color
                if "Color                        :" in line:
                    pos = line.rfind(':') + 1
                    color_value = line[pos:].strip().split(',')
                    color = [float(color_value[0]),
                             float(color_value[1]),
                             float(color_value[2]),
                             float(color_value[3])]
                # Used radius
                if "Radius used                  :" in line:
                    pos = line.rfind(':') + 1
                    radius_used = float(line[pos:].strip())
                # Covalent radius
                if "Radius, covalent             :" in line:
                    pos = line.rfind(':') + 1
                    radius_covalent = float(line[pos:].strip())
                # Atomic radius
                if "Radius, atomic               :" in line:
                    pos = line.rfind(':') + 1
                    radius_atomic = float(line[pos:].strip())
                if "Charge state                 :" in line:
                    pos = line.rfind(':') + 1
                    charge_state = float(line[pos:].strip())
                    line = data_file_p.readline()
                    pos = line.rfind(':') + 1
                    radius_ionic = float(line[pos:].strip())
                    list_radii_ionic.append(charge_state)
                    list_radii_ionic.append(radius_ionic)

                # Some Principled BSDF properties


                if "P BSDF Subsurface method     :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_subsurface_method = line[pos:].strip()
                if "P BSDF Distribution          :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_distribution = line[pos:].strip()
                if "P BSDF Subsurface Weight     :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_subsurface_weight = float(line[pos:].strip())
                if "P BSDF Subsurface Radius     :" in line:
                    pos = line.rfind(':') + 1
                    radii_values = line[pos:].strip().split(',')
                    P_BSDF_subsurface_radius = [float(color_value[0]),
                                                float(color_value[1]),
                                                float(color_value[2])]
                if "P BSDF Metallic              :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_metallic = float(line[pos:].strip())
                if "P BSDF Specular IOR Level    :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_specular_ior_level = float(line[pos:].strip())
                if "P BSDF Specular Tint         :" in line:
                    pos = line.rfind(':') + 1
                    color_value = line[pos:].strip().split(',')
                    P_BSDF_specular_tint = [float(color_value[0]),
                                            float(color_value[1]),
                                            float(color_value[2]),
                                            float(color_value[3])]
                if "P BSDF Roughness             :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_roughness = float(line[pos:].strip())
                if "P BSDF Anisotropic           :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_anisotropic = float(line[pos:].strip())
                if "P BSDF Anisotropic Rotation  :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_anisotropic_rotation = float(line[pos:].strip())
                if "P BSDF Sheen Weight          : " in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_sheen_weight = float(line[pos:].strip())
                if "P BSDF Sheen Tint            : " in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_sheen_tint = float(line[pos:].strip())
                if "P BSDF Coat Weight           :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_coat_weight = float(line[pos:].strip())
                if "P BSDF Coat Roughness        :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_coat_roughness = float(line[pos:].strip())
                if "P BSDF IOR                   :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_IOR = float(line[pos:].strip())
                if "P BSDF Transmission Weight   :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_transmission_weight = float(line[pos:].strip())
                if "P BSDF Emisssion             : " in line:
                    pos = line.rfind(':') + 1
                    color_value = line[pos:].strip().split(',')
                    P_BSDF_emission = [float(color_value[0]),
                                       float(color_value[1]),
                                       float(color_value[2]),
                                       float(color_value[3])]
                if "P BSDF Emission Strength     :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_emission_strength = float(line[pos:].strip())
                if "P BSDF Alpha                 :" in line:
                    pos = line.rfind(':') + 1
                    P_BSDF_alpha = float(line[pos:].strip())

                if "Eevee Use Backface Culling   :" in line:
                    pos = line.rfind(':') + 1
                    line = line[pos:].strip()
                    if line.lower() in ("yes", "true", "1"):
                        Eevee_use_backface = True
                    else:
                        Eevee_use_backface = False
                if "Eevee Blend Method           :" in line:
                    pos = line.rfind(':') + 1
                    Eevee_blend_method = line[pos:].strip()
                if "Eevee Shadow Method          :" in line:
                    pos = line.rfind(':') + 1
                    Eevee_shadow_method = line[pos:].strip()
                if "Eevee Clip Threshold         :" in line:
                    pos = line.rfind(':') + 1
                    Eevee_clip_threshold = float(line[pos:].strip())
                if "Eevee Use Screen Refraction  :" in line:
                    pos = line.rfind(':') + 1
                    line = line[pos:].strip()
                    if line.lower() in ("yes", "true", "1"):
                        Eevee_use_screen_refraction = True
                    else:
                        Eevee_use_screen_refraction = False
                if "Eevee Refraction depth       : " in line:
                    pos = line.rfind(':') + 1
                    Eevee_refraction_depth = float(line[pos:].strip())
                if "Eevee Use SSS Translucency   :" in line:
                    pos = line.rfind(':') + 1
                    line = line[pos:].strip()
                    if line.lower() in ("yes", "true", "1"):
                        Eevee_use_sss_translucency = True
                    else:
                        Eevee_use_sss_translucency = False
                if "Eevee Pass Index             :" in line:
                    pos = line.rfind(':') + 1
                    Eevee_pass_index = int(line[pos:].strip())


                line = data_file_p.readline()

            list_radii = [radius_used, radius_covalent, radius_atomic]

            Eevee_material = EeveeProp(Eevee_use_backface,
                                       Eevee_blend_method,
                                       Eevee_shadow_method,
                                       Eevee_clip_threshold,
                                       Eevee_use_screen_refraction,
                                       Eevee_refraction_depth,
                                       Eevee_use_sss_translucency,
                                       Eevee_pass_index)

            P_BSDF_material = PBSDFProp(P_BSDF_subsurface_method,
                                        P_BSDF_distribution,
                                        P_BSDF_subsurface_weight,
                                        P_BSDF_subsurface_radius,
                                        P_BSDF_metallic,
                                        P_BSDF_specular_ior_level,
                                        P_BSDF_specular_tint,
                                        P_BSDF_roughness,
                                        P_BSDF_anisotropic,
                                        P_BSDF_anisotropic_rotation,
                                        P_BSDF_sheen_weight,
                                        P_BSDF_sheen_tint,
                                        P_BSDF_coat_weight,
                                        P_BSDF_coat_roughness,
                                        P_BSDF_IOR,
                                        P_BSDF_transmission_weight,
                                        P_BSDF_emission,
                                        P_BSDF_emission_strength,
                                        P_BSDF_alpha)

            element = ElementProp(number,
                                  name,
                                  short_name,
                                  color,
                                  list_radii,
                                  list_radii_ionic,
                                  P_BSDF_material,
                                  Eevee_material)

            ELEMENTS.append(element)

    data_file_p.close()

    return True
