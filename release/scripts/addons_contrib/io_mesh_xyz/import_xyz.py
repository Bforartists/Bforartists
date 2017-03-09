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
from math import pi, sqrt
from mathutils import Vector, Matrix

# -----------------------------------------------------------------------------
#                                                  Atom and element data


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
# data from above via the class structure below (ElementProp). We
# have then one fixed list (above), which will never be changed, and a list of
# classes with same data. The latter can be modified via loading a separate
# custom data file for instance.
ELEMENTS = []

# This is the list, which contains all atoms of all frames! Each item is a 
# list which contains the atoms of a single frame. It is a list of  
# 'AtomProp'.
ALL_FRAMES = []

# A list of ALL balls which are put into the scene
STRUCTURE = []


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


# -----------------------------------------------------------------------------
#                                                           Some basic routines        

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


# filepath_pdb: path to pdb file
# radiustype  : '0' default
#               '1' atomic radii
#               '2' van der Waals
def read_xyz_file(filepath_xyz,radiustype):

    number_frames = 0
    total_number_atoms = 0

    # Open the file ...
    filepath_xyz_p = open(filepath_xyz, "r")

    #Go through the whole file.
    FLAG = False
    for line in filepath_xyz_p:

        # ... the loop is broken here (EOF) ...
        if line == "":
            continue

        split_list = line.rsplit()

        if len(split_list) == 1:
            number_atoms = int(split_list[0])
            FLAG = True
            
        if FLAG == True:
        
            line = filepath_xyz_p.readline()
            line = line.rstrip()
            
            all_atoms= []
            for i in range(number_atoms):


                # This is a guarantee that only the total number of atoms of the
                # first frame is used. Condition is, so far, that the number of
                # atoms in a xyz file is constant. However, sometimes the number
                # may increase (or decrease). If it decreases, the addon crashes.
                # If it increases, only the tot number of atoms of the first frame
                # is used.
                # By time, I will allow varying atom numbers ... but this takes 
                # some time ...            
                if number_frames != 0:
                    if i >= total_number_atoms:
                        break
                        
       
                line = filepath_xyz_p.readline()
                line = line.rstrip()
                split_list = line.rsplit()
                short_name = str(split_list[0])
                     
                # Go through all elements and find the element of the current atom.
                FLAG_FOUND = False
                for element in ELEMENTS:
                    if str.upper(short_name) == str.upper(element.short_name):
                        # Give the atom its proper name, color and radius:
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
                    # ... take what is written in the xyz file. These are somewhat
                    # unknown atoms. This should never happen, the element list is
                    # almost complete. However, we do this due to security reasons.
                    else:
                        name = str.upper(short_name)
                        radius = float(ELEMENTS[-2].radii[int(radiustype)])
                        color = ELEMENTS[-2].color
              
                x = float(split_list[1])
                y = float(split_list[2])
                z = float(split_list[3])
                
                location = Vector((x,y,z))
            
                all_atoms.append([short_name, name, location, radius, color])
            
            # We note here all elements. This needs to be done only once. 
            if number_frames == 0:
            
                # This is a guarantee that only the total number of atoms of the
                # first frame is used. Condition is, so far, that the number of
                # atoms in a xyz file is constant. However, sometimes the number
                # may increase (or decrease). If it decreases, the addon crashes.
                # If it increases, only the tot number of atoms of the first frame
                # is used.
                # By time, I will allow varying atom numbers ... but this takes 
                # some time ...
                total_number_atoms = number_atoms
                
                
                elements = []
                for atom in all_atoms:
                    FLAG_FOUND = False
                    for element in elements:
                        # If the atom name is already in the list, 
                        # FLAG on 'True'.
                        if element == atom[1]:
                            FLAG_FOUND = True
                            break
                    # No name in the current list has been found? => New entry.
                    if FLAG_FOUND == False:
                        # Stored are: Atom label (e.g. 'Na'), the corresponding 
                        # atom name (e.g. 'Sodium') and its color.
                        elements.append(atom[1])
            
            # Sort the atoms: create lists of atoms of one type
            structure = []
            for element in elements:
                atoms_one_type = []
                for atom in all_atoms:
                    if atom[1] == element:
                        atoms_one_type.append(AtomProp(atom[0],
                                                       atom[1],
                                                       atom[2],
                                                       atom[3],
                                                       atom[4],[]))
                structure.append(atoms_one_type)

            ALL_FRAMES.append(structure)
            number_frames += 1
            FLAG = False

    filepath_xyz_p.close()
    
    return total_number_atoms


# -----------------------------------------------------------------------------
#                                                            The main routine

def import_xyz(Ball_type,
               Ball_azimuth,
               Ball_zenith,
               Ball_radius_factor,
               radiustype,
               Ball_distance_factor,
               put_to_center, 
               put_to_center_all,
               use_camera,
               use_lamp,
               filepath_xyz):

    # List of materials
    atom_material_list = []

    # ------------------------------------------------------------------------
    # INITIALIZE THE ELEMENT LIST

    read_elements()

    # ------------------------------------------------------------------------
    # READING DATA OF ATOMS

    Number_of_total_atoms = read_xyz_file(filepath_xyz, 
                                                       radiustype)
                                               
    # We show the atoms of the first frame.
    first_frame = ALL_FRAMES[0]

    # ------------------------------------------------------------------------
    # MATERIAL PROPERTIES FOR ATOMS

    # Create first a new list of materials for each type of atom
    # (e.g. hydrogen)
    for atoms_of_one_type in first_frame:
        # Take the first atom
        atom = atoms_of_one_type[0]
        material = bpy.data.materials.new(atom.name)
        material.name = atom.name
        material.diffuse_color = atom.color
        atom_material_list.append(material)

    # Now, we go through all atoms and give them a material. For all atoms ...
    for atoms_of_one_type in first_frame:
        for atom in atoms_of_one_type:
            # ... and all materials ...
            for material in atom_material_list:
                # ... select the correct material for the current atom via
                # comparison of names ...
                if atom.name in material.name:
                    # ... and give the atom its material properties.
                    # However, before we check if it is a vacancy
                    # The vacancy is represented by a transparent cube.
                    if atom.name == "Vacancy":
                        material.transparency_method = 'Z_TRANSPARENCY'
                        material.alpha = 1.3
                        material.raytrace_transparency.fresnel = 1.6
                        material.raytrace_transparency.fresnel_factor = 1.6
                        material.use_transparency = True
                    # The atom gets its properties.
                    atom.material = material

    # ------------------------------------------------------------------------
    # TRANSLATION OF THE STRUCTURE TO THE ORIGIN

    # It may happen that the structure in a XYZ file already has an offset


    # If chosen, the structure is put into the center of the scene
    # (only the first frame).
    if put_to_center == True and put_to_center_all == False:

        sum_vec = Vector((0.0,0.0,0.0))

        # Sum of all atom coordinates
        for atoms_of_one_type in first_frame:
            sum_vec = sum([atom.location for atom in atoms_of_one_type], sum_vec)

        # Then the average is taken
        sum_vec = sum_vec / Number_of_total_atoms

        # After, for each atom the center of gravity is substracted
        for atoms_of_one_type in first_frame:
            for atom in atoms_of_one_type:
                atom.location -= sum_vec

    # If chosen, the structure is put into the center of the scene
    # (all frames).
    if put_to_center_all == True:

        # For all frames
        for frame in ALL_FRAMES: 

            sum_vec = Vector((0.0,0.0,0.0))

            # Sum of all atom coordinates
            for (i, atoms_of_one_type) in enumerate(frame):

                # This is a guarantee that only the total number of atoms of the
                # first frame is used. Condition is, so far, that the number of
                # atoms in a xyz file is constant. However, sometimes the number
                # may increase (or decrease). If it decreases, the addon crashes.
                # If it increases, only the tot number of atoms of the first frame
                # is used.
                # By time, I will allow varying atom numbers ... but this takes 
                # some time ...
                if i >= Number_of_total_atoms:
                    break

                sum_vec = sum([atom.location for atom in atoms_of_one_type], sum_vec)

            # Then the average is taken
            sum_vec = sum_vec / Number_of_total_atoms

            # After, for each atom the center of gravity is substracted
            for atoms_of_one_type in frame:
                for atom in atoms_of_one_type:
                    atom.location -= sum_vec

   
    # ------------------------------------------------------------------------
    # SCALING

    # Take all atoms and adjust their radii and scale the distances.
    for atoms_of_one_type in first_frame:
        for atom in atoms_of_one_type:
            atom.location *= Ball_distance_factor
    
    # ------------------------------------------------------------------------
    # DETERMINATION OF SOME GEOMETRIC PROPERTIES

    # In the following, some geometric properties of the whole object are
    # determined: center, size, etc.
    sum_vec = Vector((0.0,0.0,0.0))

    # First the center is determined. All coordinates are summed up ...
    for atoms_of_one_type in first_frame:
        sum_vec = sum([atom.location for atom in atoms_of_one_type], sum_vec)

    # ... and the average is taken. This gives the center of the object.
    object_center_vec = sum_vec / Number_of_total_atoms

    # Now, we determine the size.The farthest atom from the object center is
    # taken as a measure. The size is used to place well the camera and light
    # into the scene.

    object_size_vec = []
    for atoms_of_one_type in first_frame:
        object_size_vec += [atom.location - object_center_vec for atom in atoms_of_one_type]

    object_size = 0.0
    object_size = max(object_size_vec).length

    # ------------------------------------------------------------------------
    # CAMERA AND LAMP
    camera_factor = 20.0

    # If chosen a camera is put into the scene.
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
        current_layers=bpy.context.scene.layers 
        camera_data = bpy.data.cameras.new("A_camera")
        camera_data.lens = 45
        camera_data.clip_end = 500.0
        camera = bpy.data.objects.new("A_camera", camera_data)
        camera.location = camera_xyz_vec
        camera.layers = current_layers
        bpy.context.scene.objects.link(camera) 

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
        camera.select = True         
        bpy.ops.transform.rotate(value=(90.0*2*pi/360.0),
                                 axis=object_camera_vec,
                                 constraint_axis=(False, False, False),
                                 constraint_orientation='GLOBAL',
                                 mirror=False, proportional='DISABLED',
                                 proportional_edit_falloff='SMOOTH',
                                 proportional_size=1, snap=False,
                                 snap_target='CLOSEST', snap_point=(0, 0, 0),
                                 snap_align=False, snap_normal=(0, 0, 0),
                                 release_confirm=False)

    # Here a lamp is put into the scene, if chosen.
    if use_lamp == True:

        # This is the distance from the object measured in terms of %
        # of the camera distance. It is set onto 50% (1/2) distance.
        lamp_dl = sqrt(object_size) * 15 * 0.5
        # This is a factor to which extend the lamp shall go to the right
        # (from the camera  point of view).
        lamp_dy_right = lamp_dl * (3.0/4.0)

        # Create x, y and z for the lamp.
        object_lamp_vec = Vector((lamp_dl,lamp_dy_right,lamp_dl))
        lamp_xyz_vec = object_center_vec + object_lamp_vec

        # Create the lamp
        current_layers=bpy.context.scene.layers
        lamp_data = bpy.data.lamps.new(name="A_lamp", type="POINT")
        lamp_data.distance = 500.0
        lamp_data.energy = 3.0
        lamp_data.shadow_method = 'RAY_SHADOW'        
        lamp = bpy.data.objects.new("A_lamp", lamp_data)
        lamp.location = lamp_xyz_vec
        lamp.layers = current_layers
        bpy.context.scene.objects.link(lamp)         

        bpy.context.scene.world.light_settings.use_ambient_occlusion = True
        bpy.context.scene.world.light_settings.ao_factor = 0.2
        

    # ------------------------------------------------------------------------
    # DRAWING THE ATOMS

    bpy.ops.object.select_all(action='DESELECT')

    # For each list of atoms of ONE type (e.g. Hydrogen)
    for atoms_of_one_type in first_frame:

        # Create first the vertices composed of the coordinates of all
        # atoms of one type
        atom_vertices = []
        for atom in atoms_of_one_type:
            # In fact, the object is created in the World's origin.
            # This is why 'object_center_vec' is substracted. At the end
            # the whole object is translated back to 'object_center_vec'.
            atom_vertices.append( atom.location - object_center_vec )

        # Build the mesh
        atom_mesh = bpy.data.meshes.new("Mesh_"+atom.name)
        atom_mesh.from_pydata(atom_vertices, [], [])
        atom_mesh.update()
        new_atom_mesh = bpy.data.objects.new(atom.name, atom_mesh)
        bpy.context.scene.objects.link(new_atom_mesh)

        # Now, build a representative sphere (atom)
        current_layers=bpy.context.scene.layers

        if atom.name == "Vacancy":
            bpy.ops.mesh.primitive_cube_add(
                            view_align=False, enter_editmode=False,
                            location=(0.0, 0.0, 0.0),
                            rotation=(0.0, 0.0, 0.0),
                            layers=current_layers)
        else:
            # NURBS balls
            if Ball_type == "0":
                bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                            view_align=False, enter_editmode=False,
                            location=(0,0,0), rotation=(0.0, 0.0, 0.0),
                            layers=current_layers)
            # UV balls
            elif Ball_type == "1":
                bpy.ops.mesh.primitive_uv_sphere_add(
                            segments=Ball_azimuth, ring_count=Ball_zenith,
                            size=1, view_align=False, enter_editmode=False,
                            location=(0,0,0), rotation=(0, 0, 0),
                            layers=current_layers)
            # Meta balls
            elif Ball_type == "2":
                bpy.ops.object.metaball_add(type='BALL', view_align=False, 
                            enter_editmode=False, location=(0, 0, 0), 
                            rotation=(0, 0, 0), layers=current_layers)

        ball = bpy.context.scene.objects.active
        ball.scale  = (atom.radius*Ball_radius_factor,) * 3

        if atom.name == "Vacancy":
            ball.name = "Cube_"+atom.name
        else:
            ball.name = "Ball (NURBS)_"+atom.name
        ball.active_material = atom.material
        ball.parent = new_atom_mesh
        new_atom_mesh.dupli_type = 'VERTS'
        # The object is back translated to 'object_center_vec'.
        new_atom_mesh.location = object_center_vec
        STRUCTURE.append(new_atom_mesh)

    # ------------------------------------------------------------------------
    # SELECT ALL LOADED OBJECTS
    
    bpy.ops.object.select_all(action='DESELECT')
    obj = None
    for obj in STRUCTURE:
        obj.select = True
    # activate the last selected object (perhaps another should be active?)
    if obj:
        bpy.context.scene.objects.active = obj



def build_frames(frame_delta, frame_skip):

    scn = bpy.context.scene

    # Introduce the basis for all elements that appear in the structure.     
    for element in STRUCTURE:
     
        bpy.ops.object.select_all(action='DESELECT')   
        bpy.context.scene.objects.active = element
        element.select = True
        bpy.ops.object.shape_key_add(True)
        
    frame_skip += 1    

    # Introduce the keys and reference the atom positions for each key.     
    i = 0
    for j, frame in enumerate(ALL_FRAMES):        
           
        if j % frame_skip == 0:
           
            for elements_frame, elements_structure in zip(frame,STRUCTURE):
             
                key = elements_structure.shape_key_add()
    
                for atom_frame, atom_structure in zip(elements_frame, key.data):
    
                    atom_structure.co = (atom_frame.location 
                                       - elements_structure.location)
    
                key.name = atom_frame.name + "_frame_" + str(i) 

            i += 1

    num_frames = i
        
    scn.frame_start = 0
    scn.frame_end = frame_delta * num_frames

    # Manage the values of the keys
    for element in STRUCTURE:
 
        scn.frame_current = 0 

        element.data.shape_keys.key_blocks[1].value = 1.0
        element.data.shape_keys.key_blocks[2].value = 0.0
        element.data.shape_keys.key_blocks[1].keyframe_insert("value")     
        element.data.shape_keys.key_blocks[2].keyframe_insert("value")         

        scn.frame_current += frame_delta

        number = 0
    
        for number in range(num_frames)[2:]:#-1]:
    
            element.data.shape_keys.key_blocks[number-1].value = 0.0
            element.data.shape_keys.key_blocks[number].value = 1.0
            element.data.shape_keys.key_blocks[number+1].value = 0.0
            element.data.shape_keys.key_blocks[number-1].keyframe_insert("value")     
            element.data.shape_keys.key_blocks[number].keyframe_insert("value")     
            element.data.shape_keys.key_blocks[number+1].keyframe_insert("value")         
                
            scn.frame_current += frame_delta
            
        number += 1    
            
        element.data.shape_keys.key_blocks[number].value = 1.0
        element.data.shape_keys.key_blocks[number-1].value = 0.0
        element.data.shape_keys.key_blocks[number].keyframe_insert("value")     
        element.data.shape_keys.key_blocks[number-1].keyframe_insert("value")    
        


