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

import bpy
import io
import math
import os
import copy
from math import pi, cos, sin, tan, sqrt
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

ATOM_CLUSTER_ELEMENTS_DEFAULT = (
( 1,      "Hydrogen",        "H", (  1.0,   1.0,   1.0), 0.32, 0.32, 0.79 , -1 , 1.54 ),
( 2,        "Helium",       "He", ( 0.85,   1.0,   1.0), 0.93, 0.93, 0.49 ),
( 3,       "Lithium",       "Li", (  0.8,  0.50,   1.0), 1.23, 1.23, 2.05 ,  1 , 0.68 ),
( 4,     "Beryllium",       "Be", ( 0.76,   1.0,   0.0), 0.90, 0.90, 1.40 ,  1 , 0.44 ,  2 , 0.35 ),
( 5,         "Boron",        "B", (  1.0,  0.70,  0.70), 0.82, 0.82, 1.17 ,  1 , 0.35 ,  3 , 0.23 ),
( 6,        "Carbon",        "C", ( 0.56,  0.56,  0.56), 0.77, 0.77, 0.91 , -4 , 2.60 ,  4 , 0.16 ),
( 7,      "Nitrogen",        "N", ( 0.18,  0.31,  0.97), 0.75, 0.75, 0.75 , -3 , 1.71 ,  1 , 0.25 ,  3 , 0.16 ,  5 , 0.13 ),
( 8,        "Oxygen",        "O", (  1.0,  0.05,  0.05), 0.73, 0.73, 0.65 , -2 , 1.32 , -1 , 1.76 ,  1 , 0.22 ,  6 , 0.09 ),
( 9,      "Fluorine",        "F", ( 0.56,  0.87,  0.31), 0.72, 0.72, 0.57 , -1 , 1.33 ,  7 , 0.08 ),
(10,          "Neon",       "Ne", ( 0.70,  0.89,  0.96), 0.71, 0.71, 0.51 ,  1 , 1.12 ),
(11,        "Sodium",       "Na", ( 0.67,  0.36,  0.94), 1.54, 1.54, 2.23 ,  1 , 0.97 ),
(12,     "Magnesium",       "Mg", ( 0.54,   1.0,   0.0), 1.36, 1.36, 1.72 ,  1 , 0.82 ,  2 , 0.66 ),
(13,     "Aluminium",       "Al", ( 0.74,  0.65,  0.65), 1.18, 1.18, 1.82 ,  3 , 0.51 ),
(14,       "Silicon",       "Si", ( 0.94,  0.78,  0.62), 1.11, 1.11, 1.46 , -4 , 2.71 , -1 , 3.84 ,  1 , 0.65 ,  4 , 0.42 ),
(15,    "Phosphorus",        "P", (  1.0,  0.50,   0.0), 1.06, 1.06, 1.23 , -3 , 2.12 ,  3 , 0.44 ,  5 , 0.35 ),
(16,        "Sulfur",        "S", (  1.0,   1.0,  0.18), 1.02, 1.02, 1.09 , -2 , 1.84 ,  2 , 2.19 ,  4 , 0.37 ,  6 , 0.30 ),
(17,      "Chlorine",       "Cl", ( 0.12,  0.94,  0.12), 0.99, 0.99, 0.97 , -1 , 1.81 ,  5 , 0.34 ,  7 , 0.27 ),
(18,         "Argon",       "Ar", ( 0.50,  0.81,  0.89), 0.98, 0.98, 0.88 ,  1 , 1.54 ),
(19,     "Potassium",        "K", ( 0.56,  0.25,  0.83), 2.03, 2.03, 2.77 ,  1 , 0.81 ),
(20,       "Calcium",       "Ca", ( 0.23,   1.0,   0.0), 1.74, 1.74, 2.23 ,  1 , 1.18 ,  2 , 0.99 ),
(21,      "Scandium",       "Sc", ( 0.90,  0.90,  0.90), 1.44, 1.44, 2.09 ,  3 , 0.73 ),
(22,      "Titanium",       "Ti", ( 0.74,  0.76,  0.78), 1.32, 1.32, 2.00 ,  1 , 0.96 ,  2 , 0.94 ,  3 , 0.76 ,  4 , 0.68 ),
(23,      "Vanadium",        "V", ( 0.65,  0.65,  0.67), 1.22, 1.22, 1.92 ,  2 , 0.88 ,  3 , 0.74 ,  4 , 0.63 ,  5 , 0.59 ),
(24,      "Chromium",       "Cr", ( 0.54,   0.6,  0.78), 1.18, 1.18, 1.85 ,  1 , 0.81 ,  2 , 0.89 ,  3 , 0.63 ,  6 , 0.52 ),
(25,     "Manganese",       "Mn", ( 0.61,  0.47,  0.78), 1.17, 1.17, 1.79 ,  2 , 0.80 ,  3 , 0.66 ,  4 , 0.60 ,  7 , 0.46 ),
(26,          "Iron",       "Fe", ( 0.87,   0.4,   0.2), 1.17, 1.17, 1.72 ,  2 , 0.74 ,  3 , 0.64 ),
(27,        "Cobalt",       "Co", ( 0.94,  0.56,  0.62), 1.16, 1.16, 1.67 ,  2 , 0.72 ,  3 , 0.63 ),
(28,        "Nickel",       "Ni", ( 0.31,  0.81,  0.31), 1.15, 1.15, 1.62 ,  2 , 0.69 ),
(29,        "Copper",       "Cu", ( 0.78,  0.50,   0.2), 1.17, 1.17, 1.57 ,  1 , 0.96 ,  2 , 0.72 ),
(30,          "Zinc",       "Zn", ( 0.49,  0.50,  0.69), 1.25, 1.25, 1.53 ,  1 , 0.88 ,  2 , 0.74 ),
(31,       "Gallium",       "Ga", ( 0.76,  0.56,  0.56), 1.26, 1.26, 1.81 ,  1 , 0.81 ,  3 , 0.62 ),
(32,     "Germanium",       "Ge", (  0.4,  0.56,  0.56), 1.22, 1.22, 1.52 , -4 , 2.72 ,  2 , 0.73 ,  4 , 0.53 ),
(33,       "Arsenic",       "As", ( 0.74,  0.50,  0.89), 1.20, 1.20, 1.33 , -3 , 2.22 ,  3 , 0.58 ,  5 , 0.46 ),
(34,      "Selenium",       "Se", (  1.0,  0.63,   0.0), 1.16, 1.16, 1.22 , -2 , 1.91 , -1 , 2.32 ,  1 , 0.66 ,  4 , 0.50 ,  6 , 0.42 ),
(35,       "Bromine",       "Br", ( 0.65,  0.16,  0.16), 1.14, 1.14, 1.12 , -1 , 1.96 ,  5 , 0.47 ,  7 , 0.39 ),
(36,       "Krypton",       "Kr", ( 0.36,  0.72,  0.81), 1.31, 1.31, 1.24 ),
(37,      "Rubidium",       "Rb", ( 0.43,  0.18,  0.69), 2.16, 2.16, 2.98 ,  1 , 1.47 ),
(38,     "Strontium",       "Sr", (  0.0,   1.0,   0.0), 1.91, 1.91, 2.45 ,  2 , 1.12 ),
(39,       "Yttrium",        "Y", ( 0.58,   1.0,   1.0), 1.62, 1.62, 2.27 ,  3 , 0.89 ),
(40,     "Zirconium",       "Zr", ( 0.58,  0.87,  0.87), 1.45, 1.45, 2.16 ,  1 , 1.09 ,  4 , 0.79 ),
(41,       "Niobium",       "Nb", ( 0.45,  0.76,  0.78), 1.34, 1.34, 2.08 ,  1 , 1.00 ,  4 , 0.74 ,  5 , 0.69 ),
(42,    "Molybdenum",       "Mo", ( 0.32,  0.70,  0.70), 1.30, 1.30, 2.01 ,  1 , 0.93 ,  4 , 0.70 ,  6 , 0.62 ),
(43,    "Technetium",       "Tc", ( 0.23,  0.61,  0.61), 1.27, 1.27, 1.95 ,  7 , 0.97 ),
(44,     "Ruthenium",       "Ru", ( 0.14,  0.56,  0.56), 1.25, 1.25, 1.89 ,  4 , 0.67 ),
(45,       "Rhodium",       "Rh", ( 0.03,  0.49,  0.54), 1.25, 1.25, 1.83 ,  3 , 0.68 ),
(46,     "Palladium",       "Pd", (  0.0,  0.41,  0.52), 1.28, 1.28, 1.79 ,  2 , 0.80 ,  4 , 0.65 ),
(47,        "Silver",       "Ag", ( 0.75,  0.75,  0.75), 1.34, 1.34, 1.75 ,  1 , 1.26 ,  2 , 0.89 ),
(48,       "Cadmium",       "Cd", (  1.0,  0.85,  0.56), 1.48, 1.48, 1.71 ,  1 , 1.14 ,  2 , 0.97 ),
(49,        "Indium",       "In", ( 0.65,  0.45,  0.45), 1.44, 1.44, 2.00 ,  3 , 0.81 ),
(50,           "Tin",       "Sn", (  0.4,  0.50,  0.50), 1.41, 1.41, 1.72 , -4 , 2.94 , -1 , 3.70 ,  2 , 0.93 ,  4 , 0.71 ),
(51,      "Antimony",       "Sb", ( 0.61,  0.38,  0.70), 1.40, 1.40, 1.53 , -3 , 2.45 ,  3 , 0.76 ,  5 , 0.62 ),
(52,     "Tellurium",       "Te", ( 0.83,  0.47,   0.0), 1.36, 1.36, 1.42 , -2 , 2.11 , -1 , 2.50 ,  1 , 0.82 ,  4 , 0.70 ,  6 , 0.56 ),
(53,        "Iodine",        "I", ( 0.58,   0.0,  0.58), 1.33, 1.33, 1.32 , -1 , 2.20 ,  5 , 0.62 ,  7 , 0.50 ),
(54,         "Xenon",       "Xe", ( 0.25,  0.61,  0.69), 1.31, 1.31, 1.24 ),
(55,       "Caesium",       "Cs", ( 0.34,  0.09,  0.56), 2.35, 2.35, 3.35 ,  1 , 1.67 ),
(56,        "Barium",       "Ba", (  0.0,  0.78,   0.0), 1.98, 1.98, 2.78 ,  1 , 1.53 ,  2 , 1.34 ),
(57,     "Lanthanum",       "La", ( 0.43,  0.83,   1.0), 1.69, 1.69, 2.74 ,  1 , 1.39 ,  3 , 1.06 ),
(58,        "Cerium",       "Ce", (  1.0,   1.0,  0.78), 1.65, 1.65, 2.70 ,  1 , 1.27 ,  3 , 1.03 ,  4 , 0.92 ),
(59,  "Praseodymium",       "Pr", ( 0.85,   1.0,  0.78), 1.65, 1.65, 2.67 ,  3 , 1.01 ,  4 , 0.90 ),
(60,     "Neodymium",       "Nd", ( 0.78,   1.0,  0.78), 1.64, 1.64, 2.64 ,  3 , 0.99 ),
(61,    "Promethium",       "Pm", ( 0.63,   1.0,  0.78), 1.63, 1.63, 2.62 ,  3 , 0.97 ),
(62,      "Samarium",       "Sm", ( 0.56,   1.0,  0.78), 1.62, 1.62, 2.59 ,  3 , 0.96 ),
(63,      "Europium",       "Eu", ( 0.38,   1.0,  0.78), 1.85, 1.85, 2.56 ,  2 , 1.09 ,  3 , 0.95 ),
(64,    "Gadolinium",       "Gd", ( 0.27,   1.0,  0.78), 1.61, 1.61, 2.54 ,  3 , 0.93 ),
(65,       "Terbium",       "Tb", ( 0.18,   1.0,  0.78), 1.59, 1.59, 2.51 ,  3 , 0.92 ,  4 , 0.84 ),
(66,    "Dysprosium",       "Dy", ( 0.12,   1.0,  0.78), 1.59, 1.59, 2.49 ,  3 , 0.90 ),
(67,       "Holmium",       "Ho", (  0.0,   1.0,  0.61), 1.58, 1.58, 2.47 ,  3 , 0.89 ),
(68,        "Erbium",       "Er", (  0.0,  0.90,  0.45), 1.57, 1.57, 2.45 ,  3 , 0.88 ),
(69,       "Thulium",       "Tm", (  0.0,  0.83,  0.32), 1.56, 1.56, 2.42 ,  3 , 0.87 ),
(70,     "Ytterbium",       "Yb", (  0.0,  0.74,  0.21), 1.74, 1.74, 2.40 ,  2 , 0.93 ,  3 , 0.85 ),
(71,      "Lutetium",       "Lu", (  0.0,  0.67,  0.14), 1.56, 1.56, 2.25 ,  3 , 0.85 ),
(72,       "Hafnium",       "Hf", ( 0.30,  0.76,   1.0), 1.44, 1.44, 2.16 ,  4 , 0.78 ),
(73,      "Tantalum",       "Ta", ( 0.30,  0.65,   1.0), 1.34, 1.34, 2.09 ,  5 , 0.68 ),
(74,      "Tungsten",        "W", ( 0.12,  0.58,  0.83), 1.30, 1.30, 2.02 ,  4 , 0.70 ,  6 , 0.62 ),
(75,       "Rhenium",       "Re", ( 0.14,  0.49,  0.67), 1.28, 1.28, 1.97 ,  4 , 0.72 ,  7 , 0.56 ),
(76,        "Osmium",       "Os", ( 0.14,   0.4,  0.58), 1.26, 1.26, 1.92 ,  4 , 0.88 ,  6 , 0.69 ),
(77,       "Iridium",       "Ir", ( 0.09,  0.32,  0.52), 1.27, 1.27, 1.87 ,  4 , 0.68 ),
(78,     "Platinium",       "Pt", ( 0.81,  0.81,  0.87), 1.30, 1.30, 1.83 ,  2 , 0.80 ,  4 , 0.65 ),
(79,          "Gold",       "Au", (  1.0,  0.81,  0.13), 1.34, 1.34, 1.79 ,  1 , 1.37 ,  3 , 0.85 ),
(80,       "Mercury",       "Hg", ( 0.72,  0.72,  0.81), 1.49, 1.49, 1.76 ,  1 , 1.27 ,  2 , 1.10 ),
(81,      "Thallium",       "Tl", ( 0.65,  0.32,  0.30), 1.48, 1.48, 2.08 ,  1 , 1.47 ,  3 , 0.95 ),
(82,          "Lead",       "Pb", ( 0.34,  0.34,  0.38), 1.47, 1.47, 1.81 ,  2 , 1.20 ,  4 , 0.84 ),
(83,       "Bismuth",       "Bi", ( 0.61,  0.30,  0.70), 1.46, 1.46, 1.63 ,  1 , 0.98 ,  3 , 0.96 ,  5 , 0.74 ),
(84,      "Polonium",       "Po", ( 0.67,  0.36,   0.0), 1.46, 1.46, 1.53 ,  6 , 0.67 ),
(85,      "Astatine",       "At", ( 0.45,  0.30,  0.27), 1.45, 1.45, 1.43 , -3 , 2.22 ,  3 , 0.85 ,  5 , 0.46 ),
(86,         "Radon",       "Rn", ( 0.25,  0.50,  0.58), 1.00, 1.00, 1.34 ),
(87,      "Francium",       "Fr", ( 0.25,   0.0,   0.4), 1.00, 1.00, 1.00 ,  1 , 1.80 ),
(88,        "Radium",       "Ra", (  0.0,  0.49,   0.0), 1.00, 1.00, 1.00 ,  2 , 1.43 ),
(89,      "Actinium",       "Ac", ( 0.43,  0.67,  0.98), 1.00, 1.00, 1.00 ,  3 , 1.18 ),
(90,       "Thorium",       "Th", (  0.0,  0.72,   1.0), 1.65, 1.65, 1.00 ,  4 , 1.02 ),
(91,  "Protactinium",       "Pa", (  0.0,  0.63,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.13 ,  4 , 0.98 ,  5 , 0.89 ),
(92,       "Uranium",        "U", (  0.0,  0.56,   1.0), 1.42, 1.42, 1.00 ,  4 , 0.97 ,  6 , 0.80 ),
(93,     "Neptunium",       "Np", (  0.0,  0.50,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.10 ,  4 , 0.95 ,  7 , 0.71 ),
(94,     "Plutonium",       "Pu", (  0.0,  0.41,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.08 ,  4 , 0.93 ),
(95,     "Americium",       "Am", ( 0.32,  0.36,  0.94), 1.00, 1.00, 1.00 ,  3 , 1.07 ,  4 , 0.92 ),
(96,        "Curium",       "Cm", ( 0.47,  0.36,  0.89), 1.00, 1.00, 1.00 ),
(97,     "Berkelium",       "Bk", ( 0.54,  0.30,  0.89), 1.00, 1.00, 1.00 ),
(98,   "Californium",       "Cf", ( 0.63,  0.21,  0.83), 1.00, 1.00, 1.00 ),
(99,   "Einsteinium",       "Es", ( 0.70,  0.12,  0.83), 1.00, 1.00, 1.00 ),
(100,       "Fermium",       "Fm", ( 0.70,  0.12,  0.72), 1.00, 1.00, 1.00 ),
(101,   "Mendelevium",       "Md", ( 0.70,  0.05,  0.65), 1.00, 1.00, 1.00 ),
(102,      "Nobelium",       "No", ( 0.74,  0.05,  0.52), 1.00, 1.00, 1.00 ),
(103,    "Lawrencium",       "Lr", ( 0.78,   0.0,   0.4), 1.00, 1.00, 1.00 ),
(104,       "Vacancy",      "Vac", (  0.5,   0.5,   0.5), 1.00, 1.00, 1.00),
(105,       "Default",  "Default", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00),
(106,         "Stick",    "Stick", (  0.5,   0.5,   0.5), 1.00, 1.00, 1.00),
)

# This list here contains all data of the elements and will be used during
# runtime. It is a list of classes.
# During executing Atomic Blender, the list will be initialized with the fixed
# data from above via the class structure below (CLASS_atom_pdb_Elements). We
# have then one fixed list (above), which will never be changed, and a list of
# classes with same data. The latter can be modified via loading a separate
# custom data file.
ATOM_CLUSTER_ELEMENTS = []
ATOM_CLUSTER_ALL_ATOMS = []

# This is the class, which stores the properties for one element.
class CLASS_atom_cluster_Elements(object):
    __slots__ = ('number', 'name', 'short_name', 'color', 'radii', 'radii_ionic')
    def __init__(self, number, name, short_name, color, radii, radii_ionic):
        self.number = number
        self.name = name
        self.short_name = short_name
        self.color = color
        self.radii = radii
        self.radii_ionic = radii_ionic

# This is the class, which stores the properties of one atom.
class CLASS_atom_cluster_atom(object):  
    __slots__ = ('location')
    def __init__(self, location):
        self.location = location

# -----------------------------------------------------------------------------
#                                                                Read atom data
        
def DEF_atom_read_atom_data():

    del ATOM_CLUSTER_ELEMENTS[:]

    for item in ATOM_CLUSTER_ELEMENTS_DEFAULT:

        # All three radii into a list
        radii = [item[4],item[5],item[6]]
        # The handling of the ionic radii will be done later. So far, it is an
        # empty list.
        radii_ionic = []

        li = CLASS_atom_cluster_Elements(item[0],item[1],item[2],item[3],
                                         radii,radii_ionic)
        ATOM_CLUSTER_ELEMENTS.append(li)

  
# -----------------------------------------------------------------------------
#                                                           Routines for shapes

def vec_in_sphere(atom_pos,size, skin):

    regular = True
    inner   = True

    if atom_pos.length > size/2.0:
        regular = False

    if atom_pos.length < (size/2.0)*(1-skin):
        inner = False

    return (regular, inner)


def vec_in_parabole(atom_pos, height, diameter):

    regular = True
    inner   = True
      
    px = atom_pos[0]  
    py = atom_pos[1]  
    pz = atom_pos[2] + height/2.0
    
    a = diameter / sqrt(4 * height)
    
    
    if pz < 0.0:
        return (False, False)
    if px == 0.0 and py == 0.0:
        return (True, True)
         
    if py == 0.0:
        y = 0.0
        x = a * a * pz / px
        z = x * x / (a * a)
    else:
        y = pz * py * a * a / (px*px + py*py)
        x = y * px / py
        z = (x*x + y*y) / (a * a)
    
    if( atom_pos.length > sqrt(x*x+y*y+z*z) ):
        regular = False
    
    return (regular, inner)


def vec_in_pyramide_square(atom_pos, size, skin):
    
    """
    Please, if possible leave all this! The code documents the 
    mathemetical way of cutting a pyramide with square base.

    P1 = Vector((-size/2, 0.0, -size/4))
    P2 = Vector((0.0, -size/2, -size/4))
    P4 = Vector((size/2, 0.0,  -size/4))
    P5 = Vector((0.0, size/2,  -size/4))
    P6 = Vector((0.0, 0.0,      size/4))

    # First face
    v11 = P1 - P2
    v12 = P1 - P6
    n1 = v11.cross(v12)
    g1 = -n1 * P1
    
    # Second face
    v21 = P6 - P4
    v22 = P6 - P5
    n2 = v21.cross(v22)
    g2 = -n2 * P6

    # Third face
    v31 = P1 - P5
    v32 = P1 - P6
    n3 = v32.cross(v31)
    g3 = -n3 * P1
    
    # Forth face
    v41 = P6 - P2
    v42 = P2 - P4
    n4 = v41.cross(v42)
    g4 = -n4 * P2
    
    # Fith face, base
    v51 = P2 - P1
    v52 = P2 - P4
    n5 = v51.cross(v52)
    g5 = -n5 * P2
    """
 
    # A much faster way for calculation:
    size2 = size  * size
    size3 = size2 * size
    n1 = Vector((-1/4, -1/4,  1/4)) * size2
    g1 = -1/16 * size3
    n2 = Vector(( 1/4,  1/4,  1/4)) * size2
    g2 = g1
    n3 = Vector((-1/4,  1/4,  1/4)) * size2
    g3 = g1
    n4 = Vector(( 1/4, -1/4,  1/4)) * size2
    g4 = g1
    n5 = Vector(( 0.0,  0.0, -1/2)) * size2
    g5 = -1/8 * size3  

    distance_plane_1 = abs((n1 * atom_pos - g1)/n1.length)
    on_plane_1 = (atom_pos - n1 * (distance_plane_1/n1.length)).length
    distance_plane_2 = abs((n2 * atom_pos - g2)/n2.length)
    on_plane_2 = (atom_pos - n2 * (distance_plane_2/n2.length)).length
    distance_plane_3 = abs((n3 * atom_pos - g3)/n3.length)
    on_plane_3 = (atom_pos - n3 * (distance_plane_3/n3.length)).length
    distance_plane_4 = abs((n4 * atom_pos - g4)/n4.length)
    on_plane_4 = (atom_pos - n4 * (distance_plane_4/n4.length)).length
    distance_plane_5 = abs((n5 * atom_pos - g5)/n5.length)
    on_plane_5 = (atom_pos - n5 * (distance_plane_5/n5.length)).length

    regular = True
    inner   = True
    if(atom_pos.length > on_plane_1):
        regular = False
    if(atom_pos.length > on_plane_2):
        regular = False
    if(atom_pos.length > on_plane_3):
        regular = False
    if(atom_pos.length > on_plane_4):
        regular = False
    if(atom_pos.length > on_plane_5):
        regular = False

    if skin == 1.0:
        return (regular, inner)

    size = size * (1.0 - skin)
    
    size2 = size  * size
    size3 = size2 * size
    n1 = Vector((-1/4, -1/4,  1/4)) * size2
    g1 = -1/16 * size3
    n2 = Vector(( 1/4,  1/4,  1/4)) * size2
    g2 = g1
    n3 = Vector((-1/4,  1/4,  1/4)) * size2
    g3 = g1
    n4 = Vector(( 1/4, -1/4,  1/4)) * size2
    g4 = g1
    n5 = Vector(( 0.0,  0.0, -1/2)) * size2
    g5 = -1/8 * size3  

    distance_plane_1 = abs((n1 * atom_pos - g1)/n1.length)
    on_plane_1 = (atom_pos - n1 * (distance_plane_1/n1.length)).length
    distance_plane_2 = abs((n2 * atom_pos - g2)/n2.length)
    on_plane_2 = (atom_pos - n2 * (distance_plane_2/n2.length)).length
    distance_plane_3 = abs((n3 * atom_pos - g3)/n3.length)
    on_plane_3 = (atom_pos - n3 * (distance_plane_3/n3.length)).length
    distance_plane_4 = abs((n4 * atom_pos - g4)/n4.length)
    on_plane_4 = (atom_pos - n4 * (distance_plane_4/n4.length)).length
    distance_plane_5 = abs((n5 * atom_pos - g5)/n5.length)
    on_plane_5 = (atom_pos - n5 * (distance_plane_5/n5.length)).length
    
    inner = False
    if(atom_pos.length > on_plane_1):
        inner = True
    if(atom_pos.length > on_plane_2):
        inner = True
    if(atom_pos.length > on_plane_3):
        inner = True
    if(atom_pos.length > on_plane_4):
        inner = True
    if(atom_pos.length > on_plane_5):
        inner = True

    return (regular, inner)


def vec_in_pyramide_hex_abc(atom_pos, size, skin):
    
    a = size/2.0
    #c = size/2.0*cos((30/360)*2.0*pi)
    c = size * 0.4330127020
    #s = size/2.0*sin((30/360)*2.0*pi)  
    s = size * 0.25   
    #h = 2.0 * (sqrt(6.0)/3.0) * c
    h = 1.632993162 * c

    """
    Please, if possible leave all this! The code documents the 
    mathemetical way of cutting a tetraeder.

    P1 = Vector((0.0,   a, 0.0))
    P2 = Vector(( -c,  -s, 0.0))
    P3 = Vector((  c,  -s, 0.0))    
    P4 = Vector((0.0, 0.0,  h))
    C = (P1+P2+P3+P4)/4.0
    P1 = P1 - C
    P2 = P2 - C
    P3 = P3 - C
    P4 = P4 - C

    # First face
    v11 = P1 - P2
    v12 = P1 - P4
    n1 = v11.cross(v12)
    g1 = -n1 * P1
    
    # Second face
    v21 = P2 - P3
    v22 = P2 - P4
    n2 = v21.cross(v22)
    g2 = -n2 * P2

    # Third face
    v31 = P3 - P1
    v32 = P3 - P4
    n3 = v31.cross(v32)
    g3 = -n3 * P3
    
    # Forth face
    v41 = P2 - P1
    v42 = P2 - P3
    n4 = v41.cross(v42)
    g4 = -n4 * P1
    """

    n1 = Vector(( -h*(a+s),    c*h,    c*a     ))
    g1 = -1/2*c*(a*h+s*h)
    n2 = Vector((        0, -2*c*h,  2*c*s     ))
    g2 = -1/2*c*(a*h+s*h)
    n3 = Vector((  h*(a+s),    c*h,    a*c     ))
    g3 = -1/2*c*(a*h+s*h)
    n4 = Vector((        0,      0, -2*c*(s+a) ))
    g4 = -1/2*h*c*(s+a)

    distance_plane_1 = abs((n1 * atom_pos - g1)/n1.length)
    on_plane_1 = (atom_pos - n1 * (distance_plane_1/n1.length)).length
    distance_plane_2 = abs((n2 * atom_pos - g2)/n2.length)
    on_plane_2 = (atom_pos - n2 * (distance_plane_2/n2.length)).length
    distance_plane_3 = abs((n3 * atom_pos - g3)/n3.length)
    on_plane_3 = (atom_pos - n3 * (distance_plane_3/n3.length)).length
    distance_plane_4 = abs((n4 * atom_pos - g4)/n4.length)
    on_plane_4 = (atom_pos - n4 * (distance_plane_4/n4.length)).length

    regular = True
    inner   = True
    if(atom_pos.length > on_plane_1):
        regular = False
    if(atom_pos.length > on_plane_2):
        regular = False
    if(atom_pos.length > on_plane_3):
        regular = False
    if(atom_pos.length > on_plane_4):
        regular = False

    if skin == 1.0:
        return (regular, inner)

    size = size * (1.0 - skin)
    
    a = size/2.0
    #c = size/2.0*cos((30/360)*2.0*pi)
    c= size * 0.4330127020
    #s = size/2.0*sin((30/360)*2.0*pi)  
    s = size * 0.25   
    #h = 2.0 * (sqrt(6.0)/3.0) * c
    h = 1.632993162 * c

    n1 = Vector(( -h*(a+s),    c*h,    c*a     ))
    g1 = -1/2*c*(a*h+s*h)
    n2 = Vector((        0, -2*c*h,  2*c*s     ))
    g2 = -1/2*c*(a*h+s*h)
    n3 = Vector((  h*(a+s),    c*h,    a*c     ))
    g3 = -1/2*c*(a*h+s*h)
    n4 = Vector((        0,      0, -2*c*(s+a) ))
    g4 = -1/2*h*c*(s+a)

    distance_plane_1 = abs((n1 * atom_pos - g1)/n1.length)
    on_plane_1 = (atom_pos - n1 * (distance_plane_1/n1.length)).length
    distance_plane_2 = abs((n2 * atom_pos - g2)/n2.length)
    on_plane_2 = (atom_pos - n2 * (distance_plane_2/n2.length)).length
    distance_plane_3 = abs((n3 * atom_pos - g3)/n3.length)
    on_plane_3 = (atom_pos - n3 * (distance_plane_3/n3.length)).length
    distance_plane_4 = abs((n4 * atom_pos - g4)/n4.length)
    on_plane_4 = (atom_pos - n4 * (distance_plane_4/n4.length)).length
    
    inner = False
    if(atom_pos.length > on_plane_1):
        inner = True
    if(atom_pos.length > on_plane_2):
        inner = True
    if(atom_pos.length > on_plane_3):
        inner = True
    if(atom_pos.length > on_plane_4):
        inner = True

    return (regular, inner)
    


def vec_in_octahedron(atom_pos,size, skin):

    regular = True
    inner   = True

    """
    Please, if possible leave all this! The code documents the 
    mathemetical way of cutting an octahedron.

    P1 = Vector((-size/2, 0.0, 0.0))
    P2 = Vector((0.0, -size/2, 0.0))
    P3 = Vector((0.0, 0.0, -size/2))
    P4 = Vector((size/2, 0.0, 0.0))
    P5 = Vector((0.0, size/2, 0.0))
    P6 = Vector((0.0, 0.0, size/2))

    # First face
    v11 = P2 - P1
    v12 = P2 - P3
    n1 = v11.cross(v12)
    g1 = -n1 * P2
    
    # Second face
    v21 = P1 - P5
    v22 = P1 - P3
    n2 = v21.cross(v22)
    g2 = -n2 * P1 
    
    # Third face
    v31 = P1 - P2
    v32 = P1 - P6
    n3 = v31.cross(v32)
    g3 = -n3 * P1
    
    # Forth face
    v41 = P6 - P2
    v42 = P2 - P4
    n4 = v41.cross(v42)
    g4 = -n4 * P2

    # Fith face
    v51 = P2 - P3
    v52 = P2 - P4
    n5 = v51.cross(v52)
    g5 = -n5 * P2

    # Six face
    v61 = P6 - P4
    v62 = P6 - P5
    n6 = v61.cross(v62)
    g6 = -n6 * P6

    # Seventh face
    v71 = P5 - P4
    v72 = P5 - P3
    n7 = v71.cross(v72)
    g7 = -n7 * P5

    # Eigth face
    v81 = P1 - P5
    v82 = P1 - P6
    n8 = v82.cross(v81)
    g8 = -n8 * P1
    """
 
    # A much faster way for calculation:
    size2 = size  * size
    size3 = size2 * size
    n1 = Vector((-1/4, -1/4, -1/4)) * size2
    g1 = -1/8 * size3
    n2 = Vector((-1/4,  1/4, -1/4)) * size2
    g2 = g1
    n3 = Vector((-1/4, -1/4,  1/4)) * size2
    g3 = g1
    n4 = Vector(( 1/4, -1/4,  1/4)) * size2
    g4 = g1
    n5 = Vector(( 1/4, -1/4, -1/4)) * size2
    g5 = g1
    n6 = Vector(( 1/4,  1/4,  1/4)) * size2
    g6 = g1
    n7 = Vector(( 1/4,  1/4, -1/4)) * size2
    g7 = g1
    n8 = Vector((-1/4,  1/4,  1/4)) * size2
    g8 = g1

    distance_plane_1 = abs((n1 * atom_pos - g1)/n1.length)
    on_plane_1 = (atom_pos - n1 * (distance_plane_1/n1.length)).length
    distance_plane_2 = abs((n2 * atom_pos - g2)/n2.length)
    on_plane_2 = (atom_pos - n2 * (distance_plane_2/n2.length)).length
    distance_plane_3 = abs((n3 * atom_pos - g3)/n3.length)
    on_plane_3 = (atom_pos - n3 * (distance_plane_3/n3.length)).length
    distance_plane_4 = abs((n4 * atom_pos - g4)/n4.length)
    on_plane_4 = (atom_pos - n4 * (distance_plane_4/n4.length)).length
    distance_plane_5 = abs((n5 * atom_pos - g5)/n5.length)
    on_plane_5 = (atom_pos - n5 * (distance_plane_5/n5.length)).length
    distance_plane_6 = abs((n6 * atom_pos - g6)/n6.length)
    on_plane_6 = (atom_pos - n6 * (distance_plane_6/n6.length)).length
    distance_plane_7 = abs((n7 * atom_pos - g7)/n7.length)
    on_plane_7 = (atom_pos - n7 * (distance_plane_7/n7.length)).length
    distance_plane_8 = abs((n8 * atom_pos - g8)/n8.length)
    on_plane_8 = (atom_pos - n8 * (distance_plane_8/n8.length)).length

    if(atom_pos.length > on_plane_1):
        regular = False
    if(atom_pos.length > on_plane_2):
        regular = False
    if(atom_pos.length > on_plane_3):
        regular = False
    if(atom_pos.length > on_plane_4):
        regular = False
    if(atom_pos.length > on_plane_5):
        regular = False
    if(atom_pos.length > on_plane_6):
        regular = False
    if(atom_pos.length > on_plane_7):
        regular = False
    if(atom_pos.length > on_plane_8):
        regular = False

    if skin == 1.0:
        return (regular, inner)

    size = size * (1.0 - skin)

    size2 = size  * size
    size3 = size2 * size
    n1 = Vector((-1/4, -1/4, -1/4)) * size2
    g1 = -1/8 * size3
    n2 = Vector((-1/4,  1/4, -1/4)) * size2
    g2 = g1
    n3 = Vector((-1/4, -1/4,  1/4)) * size2
    g3 = g1
    n4 = Vector(( 1/4, -1/4,  1/4)) * size2
    g4 = g1
    n5 = Vector(( 1/4, -1/4, -1/4)) * size2
    g5 = g1
    n6 = Vector(( 1/4,  1/4,  1/4)) * size2
    g6 = g1
    n7 = Vector(( 1/4,  1/4, -1/4)) * size2
    g7 = g1
    n8 = Vector((-1/4,  1/4,  1/4)) * size2
    g8 = g1

    distance_plane_1 = abs((n1 * atom_pos - g1)/n1.length)
    on_plane_1 = (atom_pos - n1 * (distance_plane_1/n1.length)).length
    distance_plane_2 = abs((n2 * atom_pos - g2)/n2.length)
    on_plane_2 = (atom_pos - n2 * (distance_plane_2/n2.length)).length
    distance_plane_3 = abs((n3 * atom_pos - g3)/n3.length)
    on_plane_3 = (atom_pos - n3 * (distance_plane_3/n3.length)).length
    distance_plane_4 = abs((n4 * atom_pos - g4)/n4.length)
    on_plane_4 = (atom_pos - n4 * (distance_plane_4/n4.length)).length
    distance_plane_5 = abs((n5 * atom_pos - g5)/n5.length)
    on_plane_5 = (atom_pos - n5 * (distance_plane_5/n5.length)).length
    distance_plane_6 = abs((n6 * atom_pos - g6)/n6.length)
    on_plane_6 = (atom_pos - n6 * (distance_plane_6/n6.length)).length
    distance_plane_7 = abs((n7 * atom_pos - g7)/n7.length)
    on_plane_7 = (atom_pos - n7 * (distance_plane_7/n7.length)).length
    distance_plane_8 = abs((n8 * atom_pos - g8)/n8.length)
    on_plane_8 = (atom_pos - n8 * (distance_plane_8/n8.length)).length

    inner = False
    if(atom_pos.length > on_plane_1):
        inner = True
    if(atom_pos.length > on_plane_2):
        inner = True
    if(atom_pos.length > on_plane_3):
        inner = True
    if(atom_pos.length > on_plane_4):
        inner = True
    if(atom_pos.length > on_plane_5):
        inner = True
    if(atom_pos.length > on_plane_6):
        inner = True
    if(atom_pos.length > on_plane_7):
        inner = True
    if(atom_pos.length > on_plane_8):
        inner = True

    return (regular, inner)


def vec_in_truncated_octahedron(atom_pos,size, skin):

    regular = True
    inner   = True

    # The normal octahedron
    size2 = size  * size
    size3 = size2 * size
    n1 = Vector((-1/4, -1/4, -1/4)) * size2
    g1 = -1/8 * size3
    n2 = Vector((-1/4,  1/4, -1/4)) * size2
    g2 = g1
    n3 = Vector((-1/4, -1/4,  1/4)) * size2
    g3 = g1
    n4 = Vector(( 1/4, -1/4,  1/4)) * size2
    g4 = g1
    n5 = Vector(( 1/4, -1/4, -1/4)) * size2
    g5 = g1
    n6 = Vector(( 1/4,  1/4,  1/4)) * size2
    g6 = g1
    n7 = Vector(( 1/4,  1/4, -1/4)) * size2
    g7 = g1
    n8 = Vector((-1/4,  1/4,  1/4)) * size2
    g8 = g1

    distance_plane_1 = abs((n1 * atom_pos - g1)/n1.length)
    on_plane_1 = (atom_pos - n1 * (distance_plane_1/n1.length)).length
    distance_plane_2 = abs((n2 * atom_pos - g2)/n2.length)
    on_plane_2 = (atom_pos - n2 * (distance_plane_2/n2.length)).length
    distance_plane_3 = abs((n3 * atom_pos - g3)/n3.length)
    on_plane_3 = (atom_pos - n3 * (distance_plane_3/n3.length)).length
    distance_plane_4 = abs((n4 * atom_pos - g4)/n4.length)
    on_plane_4 = (atom_pos - n4 * (distance_plane_4/n4.length)).length
    distance_plane_5 = abs((n5 * atom_pos - g5)/n5.length)
    on_plane_5 = (atom_pos - n5 * (distance_plane_5/n5.length)).length
    distance_plane_6 = abs((n6 * atom_pos - g6)/n6.length)
    on_plane_6 = (atom_pos - n6 * (distance_plane_6/n6.length)).length
    distance_plane_7 = abs((n7 * atom_pos - g7)/n7.length)
    on_plane_7 = (atom_pos - n7 * (distance_plane_7/n7.length)).length
    distance_plane_8 = abs((n8 * atom_pos - g8)/n8.length)
    on_plane_8 = (atom_pos - n8 * (distance_plane_8/n8.length)).length

    # Here are the 6 additional faces
    # pp = (size/2.0) - (sqrt(2.0)/2.0) * ((size/sqrt(2.0))/3.0)
    pp = size / 3.0

    n_1 = Vector((1.0,0.0,0.0)) 
    n_2 = Vector((-1.0,0.0,0.0))           
    n_3 = Vector((0.0,1.0,0.0))    
    n_4 = Vector((0.0,-1.0,0.0))
    n_5 = Vector((0.0,0.0,1.0))    
    n_6 = Vector((0.0,0.0,-1.0))   

    distance_plane_1b = abs((n_1 * atom_pos + pp)/n_1.length)
    on_plane_1b = (atom_pos - n_1 * (distance_plane_1b/n_1.length)).length
    distance_plane_2b = abs((n_2 * atom_pos + pp)/n_2.length)
    on_plane_2b = (atom_pos - n_2 * (distance_plane_2b/n_2.length)).length
    distance_plane_3b = abs((n_3 * atom_pos + pp)/n_3.length)
    on_plane_3b = (atom_pos - n_3 * (distance_plane_3b/n_3.length)).length
    distance_plane_4b = abs((n_4 * atom_pos + pp)/n_4.length)
    on_plane_4b = (atom_pos - n_4 * (distance_plane_4b/n_4.length)).length
    distance_plane_5b = abs((n_5 * atom_pos + pp)/n_5.length)
    on_plane_5b = (atom_pos - n_5 * (distance_plane_5b/n_5.length)).length
    distance_plane_6b = abs((n_6 * atom_pos + pp)/n_6.length)
    on_plane_6b = (atom_pos - n_6 * (distance_plane_6b/n_6.length)).length

    if(atom_pos.length > on_plane_1):
        regular = False
    if(atom_pos.length > on_plane_2):
        regular = False
    if(atom_pos.length > on_plane_3):
        regular = False
    if(atom_pos.length > on_plane_4):
        regular = False
    if(atom_pos.length > on_plane_5):
        regular = False
    if(atom_pos.length > on_plane_6):
        regular = False
    if(atom_pos.length > on_plane_7):
        regular = False
    if(atom_pos.length > on_plane_8):
        regular = False
    if(atom_pos.length > on_plane_1b):
        regular = False
    if(atom_pos.length > on_plane_2b):
        regular = False
    if(atom_pos.length > on_plane_3b):
        regular = False
    if(atom_pos.length > on_plane_4b):
        regular = False
    if(atom_pos.length > on_plane_5b):
        regular = False
    if(atom_pos.length > on_plane_6b):
        regular = False

    if skin == 1.0:
        return (regular, inner)

    size = size * (1.0 - skin)
    
    # The normal octahedron
    size2 = size  * size
    size3 = size2 * size
    n1 = Vector((-1/4, -1/4, -1/4)) * size2
    g1 = -1/8 * size3
    n2 = Vector((-1/4,  1/4, -1/4)) * size2
    g2 = g1
    n3 = Vector((-1/4, -1/4,  1/4)) * size2
    g3 = g1
    n4 = Vector(( 1/4, -1/4,  1/4)) * size2
    g4 = g1
    n5 = Vector(( 1/4, -1/4, -1/4)) * size2
    g5 = g1
    n6 = Vector(( 1/4,  1/4,  1/4)) * size2
    g6 = g1
    n7 = Vector(( 1/4,  1/4, -1/4)) * size2
    g7 = g1
    n8 = Vector((-1/4,  1/4,  1/4)) * size2
    g8 = g1

    distance_plane_1 = abs((n1 * atom_pos - g1)/n1.length)
    on_plane_1 = (atom_pos - n1 * (distance_plane_1/n1.length)).length
    distance_plane_2 = abs((n2 * atom_pos - g2)/n2.length)
    on_plane_2 = (atom_pos - n2 * (distance_plane_2/n2.length)).length
    distance_plane_3 = abs((n3 * atom_pos - g3)/n3.length)
    on_plane_3 = (atom_pos - n3 * (distance_plane_3/n3.length)).length
    distance_plane_4 = abs((n4 * atom_pos - g4)/n4.length)
    on_plane_4 = (atom_pos - n4 * (distance_plane_4/n4.length)).length
    distance_plane_5 = abs((n5 * atom_pos - g5)/n5.length)
    on_plane_5 = (atom_pos - n5 * (distance_plane_5/n5.length)).length
    distance_plane_6 = abs((n6 * atom_pos - g6)/n6.length)
    on_plane_6 = (atom_pos - n6 * (distance_plane_6/n6.length)).length
    distance_plane_7 = abs((n7 * atom_pos - g7)/n7.length)
    on_plane_7 = (atom_pos - n7 * (distance_plane_7/n7.length)).length
    distance_plane_8 = abs((n8 * atom_pos - g8)/n8.length)
    on_plane_8 = (atom_pos - n8 * (distance_plane_8/n8.length)).length

    # Here are the 6 additional faces
    # pp = (size/2.0) - (sqrt(2.0)/2.0) * ((size/sqrt(2.0))/3.0)
    pp = size / 3.0

    n_1 = Vector((1.0,0.0,0.0)) 
    n_2 = Vector((-1.0,0.0,0.0))           
    n_3 = Vector((0.0,1.0,0.0))    
    n_4 = Vector((0.0,-1.0,0.0))
    n_5 = Vector((0.0,0.0,1.0))    
    n_6 = Vector((0.0,0.0,-1.0))   
    
    distance_plane_1b = abs((n_1 * atom_pos + pp)/n_1.length)
    on_plane_1b = (atom_pos - n_1 * (distance_plane_1b/n_1.length)).length
    distance_plane_2b = abs((n_2 * atom_pos + pp)/n_2.length)
    on_plane_2b = (atom_pos - n_2 * (distance_plane_2b/n_2.length)).length
    distance_plane_3b = abs((n_3 * atom_pos + pp)/n_3.length)
    on_plane_3b = (atom_pos - n_3 * (distance_plane_3b/n_3.length)).length
    distance_plane_4b = abs((n_4 * atom_pos + pp)/n_4.length)
    on_plane_4b = (atom_pos - n_4 * (distance_plane_4b/n_4.length)).length
    distance_plane_5b = abs((n_5 * atom_pos + pp)/n_5.length)
    on_plane_5b = (atom_pos - n_5 * (distance_plane_5b/n_5.length)).length
    distance_plane_6b = abs((n_6 * atom_pos + pp)/n_6.length)
    on_plane_6b = (atom_pos - n_6 * (distance_plane_6b/n_6.length)).length

    inner = False

    if(atom_pos.length > on_plane_1):
        inner = True
    if(atom_pos.length > on_plane_2):
        inner = True
    if(atom_pos.length > on_plane_3):
        inner = True
    if(atom_pos.length > on_plane_4):
        inner = True
    if(atom_pos.length > on_plane_5):
        inner = True
    if(atom_pos.length > on_plane_6):
        inner = True
    if(atom_pos.length > on_plane_7):
        inner = True
    if(atom_pos.length > on_plane_8):
        inner = True
    if(atom_pos.length > on_plane_1b):
        inner = True
    if(atom_pos.length > on_plane_2b):
        inner = True
    if(atom_pos.length > on_plane_3b):
        inner = True
    if(atom_pos.length > on_plane_4b):
        inner = True
    if(atom_pos.length > on_plane_5b):
        inner = True
    if(atom_pos.length > on_plane_6b):
        inner = True
    
    return (regular, inner)

# -----------------------------------------------------------------------------
#                                                         Routines for lattices

def create_hexagonal_abcabc_lattice(ctype, size, skin, lattice):

    atom_number_total = 0
    atom_number_drawn = 0
    y_displ = 0
    z_displ = 0

    """
    e = (1/sqrt(2.0)) * lattice
    f = sqrt(3.0/4.0) * e
    df1 = (e/2.0) * tan((30.0/360.0)*2.0*pi)
    df2 = (e/2.0) / cos((30.0/360.0)*2.0*pi)
    g = sqrt(2.0/3.0) * e
    """

    e = 0.7071067810 * lattice
    f = 0.8660254038 * e
    df1 = 0.2886751348 * e
    df2 = 0.5773502690 * e
    g = 0.8164965810 * e

    if ctype == "parabolid_abc":
        # size = height, skin = diameter
        number_x = int(skin/(2*e))+4
        number_y = int(skin/(2*f))+4
        number_z = int(size/(2*g))
    else:
        number_x = int(size/(2*e))+4
        number_y = int(size/(2*f))+4
        number_z = int(size/(2*g))+1+4


    for k in range(-number_z,number_z+1):
        for j in range(-number_y,number_y+1):
            for i in range(-number_x,number_x+1):
                atom = Vector((float(i)*e,float(j)*f,float(k)*g)) 

                if y_displ == 1:
                    if z_displ == 1:
                        atom[0] += e/2.0  
                    else:
                        atom[0] -= e/2.0
                if z_displ == 1:
                    atom[0] -= e/2.0
                    atom[1] += df1
                if z_displ == 2:
                    atom[0] += 0.0
                    atom[1] += df2

                if ctype == "sphere_hex_abc":
                    message = vec_in_sphere(atom, size, skin)
                elif ctype == "pyramide_hex_abc":
                    # size = height, skin = diameter
                    message = vec_in_pyramide_hex_abc(atom, size, skin)
                elif ctype == "parabolid_abc":
                    message = vec_in_parabole(atom, size, skin)          

                if message[0] == True and message[1] == True:
                    atom_add = CLASS_atom_cluster_atom(atom)
                    ATOM_CLUSTER_ALL_ATOMS.append(atom_add)
                    atom_number_total += 1
                    atom_number_drawn += 1
                if message[0] == True and message[1] == False:
                    atom_number_total += 1                 
          
            if y_displ == 1:
                y_displ = 0
            else:
                y_displ = 1

        y_displ = 0
        if z_displ == 0:
           z_displ = 1
        elif z_displ == 1:
           z_displ = 2
        else:
           z_displ = 0

    print("Atom positions calculated")

    return (atom_number_total, atom_number_drawn)


def create_hexagonal_abab_lattice(ctype, size, skin, lattice):

    atom_number_total = 0
    atom_number_drawn = 0
    y_displ = "even"
    z_displ = "even"

    """
    e = (1/sqrt(2.0)) * lattice
    f = sqrt(3.0/4.0) * e
    df = (e/2.0) * tan((30.0/360.0)*2*pi)
    g = sqrt(2.0/3.0) * e
    """

    e = 0.7071067814 * lattice
    f = 0.8660254038 * e
    df = 0.2886751348 * e
    g = 0.8164965810 * e


    if ctype == "parabolid_ab":
        # size = height, skin = diameter
        number_x = int(skin/(2*e))+4
        number_y = int(skin/(2*f))+4
        number_z = int(size/(2*g))
    else:
        number_x = int(size/(2*e))+4
        number_y = int(size/(2*f))+4
        number_z = int(size/(2*g))+1+4


    for k in range(-number_z,number_z+1):
        for j in range(-number_y,number_y+1):
            for i in range(-number_x,number_x+1):

                atom = Vector((float(i)*e,float(j)*f,float(k)*g))
          
                if "odd" in y_displ:
                    if "odd" in z_displ:
                        atom[0] += e/2.0  
                    else:
                        atom[0] -= e/2.0
                if "odd" in z_displ:
                    atom[0] -= e/2.0
                    atom[1] += df

                if ctype == "sphere_hex_ab":
                    message = vec_in_sphere(atom, size, skin)
                elif ctype == "parabolid_ab":
                    # size = height, skin = diameter
                    message = vec_in_parabole(atom, size, skin)          
          
                if message[0] == True and message[1] == True:
                    atom_add = CLASS_atom_cluster_atom(atom)
                    ATOM_CLUSTER_ALL_ATOMS.append(atom_add)
                    atom_number_total += 1
                    atom_number_drawn += 1
                if message[0] == True and message[1] == False:
                    atom_number_total += 1  
          
            if "even" in y_displ:
                y_displ = "odd"
            else:
                y_displ = "even"

        y_displ = "even"
        if "even" in z_displ:
            z_displ = "odd"
        else:
            z_displ = "even"

    print("Atom positions calculated")

    return (atom_number_total, atom_number_drawn)


def create_square_lattice(ctype, size, skin, lattice):

    atom_number_total = 0
    atom_number_drawn = 0
    
    if ctype == "parabolid_square":
        # size = height, skin = diameter
        number_k = int(size/(2.0*lattice))
        number_j = int(skin/(2.0*lattice)) + 5
        number_i = int(skin/(2.0*lattice)) + 5
    else:
        number_k = int(size/(2.0*lattice))
        number_j = int(size/(2.0*lattice))
        number_i = int(size/(2.0*lattice))       


    for k in range(-number_k,number_k+1):
        for j in range(-number_j,number_j+1):
            for i in range(-number_i,number_i+1):

                atom = Vector((float(i),float(j),float(k))) * lattice 

                if ctype == "sphere_square":
                    message = vec_in_sphere(atom, size, skin)
                elif ctype == "pyramide_square":
                    message = vec_in_pyramide_square(atom, size, skin)
                elif ctype == "parabolid_square":
                    # size = height, skin = diameter
                    message = vec_in_parabole(atom, size, skin)          
                elif ctype == "octahedron":
                    message = vec_in_octahedron(atom, size, skin)            
                elif ctype == "truncated_octahedron":
                    message = vec_in_truncated_octahedron(atom,size, skin)

                if message[0] == True and message[1] == True:
                    atom_add = CLASS_atom_cluster_atom(atom)
                    ATOM_CLUSTER_ALL_ATOMS.append(atom_add)
                    atom_number_total += 1
                    atom_number_drawn += 1
                if message[0] == True and message[1] == False:
                    atom_number_total += 1 

    print("Atom positions calculated")

    return (atom_number_total, atom_number_drawn)



# -----------------------------------------------------------------------------
#                                                   Routine for the icosahedron


# Note that the icosahedron needs a special treatment since it requires a
# non-common crystal lattice. The faces are (111) facets and the geometry
# is five-fold. So far, a max size of 8217 atoms can be chosen.
# More details about icosahedron shaped clusters can be found in:
#
# 1. C. Mottet, G. Tréglia, B. Legrand, Surface Science 383 (1997) L719-L727
# 2. C. R. Henry, Surface Science Reports 31 (1998) 231-325

# The following code is a translation from an existing Fortran code into Python.
# The Fortran code has been created by Christine Mottet and translated by me
# (Clemens Barth). 

# Although a couple of code lines are non-typical for Python, it is best to
# leave the code as is.
#
# To do:
#
# 1. Unlimited cluster size
# 2. Skin effect

def create_icosahedron(size, lattice):

    natot = int(1 + (10*size*size+15*size+11)*size/3)

    x = list(range(natot+1))
    y = list(range(natot+1))
    z = list(range(natot+1))

    xs = list(range(12+1))
    ys = list(range(12+1))
    zs = list(range(12+1))

    xa = [[[ [] for i in range(12+1)] for j in range(12+1)] for k in range(20+1)]
    ya = [[[ [] for i in range(12+1)] for j in range(12+1)] for k in range(20+1)]
    za = [[[ [] for i in range(12+1)] for j in range(12+1)] for k in range(20+1)]

    naret  = [[ [] for i in range(12+1)] for j in range(12+1)]
    nfacet = [[[ [] for i in range(12+1)] for j in range(12+1)] for k in range(12+1)]

    rac2 = sqrt(2.0)
    rac5 = sqrt(5.0)
    tdef = (rac5+1.0)/2.0

    rapp  = sqrt(2.0*(1.0-tdef/(tdef*tdef+1.0)))
    nats  = 2 * (5*size*size+1)
    nat   = 13
    epsi  = 0.01

    x[1] = 0.0
    y[1] = 0.0
    z[1] = 0.0

    for i in range(2, 5+1):
        z[i]   = 0.0
        y[i+4] = 0.0
        x[i+8] = 0.0
    
    for i in range(2, 3+1):
        x[i]    =  tdef
        x[i+2]  = -tdef
        x[i+4]  =  1.0
        x[i+6]  = -1.0
        y[i+8]  =  tdef
        y[i+10] = -tdef

    for i in range(2, 4+1, 2):
        y[i]   =  1.0
        y[i+1] = -1.0
        z[i+4] =  tdef
        z[i+5] = -tdef
        z[i+8] =  1.0
        z[i+9] = -1.0

    xdef = rac2 / sqrt(tdef * tdef + 1)

    for i in range(2, 13+1):
        x[i] = x[i] * xdef / 2.0
        y[i] = y[i] * xdef / 2.0
        z[i] = z[i] * xdef / 2.0

    if size > 1:

        for n in range (2, size+1):
            ifacet = 0
            iaret  = 0
            inatf  = 0
            for i in range(1, 12+1):
                for j in range(1, 12+1):
                    naret[i][j] = 0
                    for k in range (1, 12+1): 
                        nfacet[i][j][k] = 0

            nl1 = 6
            nl2 = 8
            nl3 = 9
            k1  = 0
            k2  = 0
            k3  = 0
            k12 = 0
            for i in range(1, 12+1):
                nat += 1
                xs[i] = n * x[i+1]
                ys[i] = n * y[i+1]
                zs[i] = n * z[i+1]
                x[nat] = xs[i]
                y[nat] = ys[i]
                z[nat] = zs[i]
                k1 += 1

            for i in range(1, 12+1):
                for j in range(2, 12+1):
                    if j <= i:
                        continue
                    
                    xij = xs[j] - xs[i]
                    yij = ys[j] - ys[i]
                    zij = zs[j] - zs[i]
                    xij2 = xij * xij
                    yij2 = yij * yij
                    zij2 = zij * zij
                    dij2 = xij2 + yij2 + zij2
                    dssn = n * rapp / rac2
                    dssn2 = dssn * dssn
                    diffij = abs(dij2-dssn2)
                    if diffij >= epsi:
                        continue
                    
                    for k in range(3, 12+1):
                        if k <= j:
                            continue
                        
                        xjk = xs[k] - xs[j]
                        yjk = ys[k] - ys[j]
                        zjk = zs[k] - zs[j]
                        xjk2 = xjk * xjk
                        yjk2 = yjk * yjk
                        zjk2 = zjk * zjk
                        djk2 = xjk2 + yjk2 + zjk2
                        diffjk = abs(djk2-dssn2)
                        if diffjk >= epsi:
                            continue
                        
                        xik = xs[k] - xs[i]
                        yik = ys[k] - ys[i]
                        zik = zs[k] - zs[i]
                        xik2 = xik * xik
                        yik2 = yik * yik
                        zik2 = zik * zik
                        dik2 = xik2 + yik2 + zik2
                        diffik = abs(dik2-dssn2)
                        if diffik >= epsi:
                            continue
                        
                        if nfacet[i][j][k] != 0:
                            continue

                        ifacet += 1
                        nfacet[i][j][k] = ifacet

                        if naret[i][j] == 0:
                            iaret += 1
                            naret[i][j] = iaret
                            for l in range(1,n-1+1):
                                nat += 1
                                xa[i][j][l] = xs[i]+l*(xs[j]-xs[i]) / n
                                ya[i][j][l] = ys[i]+l*(ys[j]-ys[i]) / n
                                za[i][j][l] = zs[i]+l*(zs[j]-zs[i]) / n
                                x[nat] = xa[i][j][l]
                                y[nat] = ya[i][j][l]
                                z[nat] = za[i][j][l]

                        if naret[i][k] == 0:
                            iaret += 1
                            naret[i][k] = iaret
                            for l in range(1, n-1+1):
                                nat += 1
                                xa[i][k][l] = xs[i]+l*(xs[k]-xs[i]) / n
                                ya[i][k][l] = ys[i]+l*(ys[k]-ys[i]) / n
                                za[i][k][l] = zs[i]+l*(zs[k]-zs[i]) / n
                                x[nat] = xa[i][k][l]
                                y[nat] = ya[i][k][l]
                                z[nat] = za[i][k][l]

                        if naret[j][k] == 0:
                            iaret += 1
                            naret[j][k] = iaret
                            for l in range(1, n-1+1):
                                nat += 1
                                xa[j][k][l] = xs[j]+l*(xs[k]-xs[j]) / n
                                ya[j][k][l] = ys[j]+l*(ys[k]-ys[j]) / n
                                za[j][k][l] = zs[j]+l*(zs[k]-zs[j]) / n
                                x[nat] = xa[j][k][l]
                                y[nat] = ya[j][k][l]
                                z[nat] = za[j][k][l]

                        for l in range(2, n-1+1):
                            for ll in range(1, l-1+1):
                                xf = xa[i][j][l]+ll*(xa[i][k][l]-xa[i][j][l]) / l
                                yf = ya[i][j][l]+ll*(ya[i][k][l]-ya[i][j][l]) / l
                                zf = za[i][j][l]+ll*(za[i][k][l]-za[i][j][l]) / l
                                nat += 1
                                inatf += 1
                                x[nat] = xf
                                y[nat] = yf
                                z[nat] = zf
                                k3 += 1

    atom_number_total = 0
    atom_number_drawn = 0

    for i in range (1,natot+1):

        atom = Vector((x[i],y[i],z[i])) * lattice 

        atom_add = CLASS_atom_cluster_atom(atom)
        ATOM_CLUSTER_ALL_ATOMS.append(atom_add)
        atom_number_total += 1
        atom_number_drawn += 1

    return (atom_number_total, atom_number_drawn)

















