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

# The list 'ELEMENTS' contains all data of the elements and will be used during
# runtime. The list will be initialized with the fixed
# data from above via the class below (ElementProp). One fixed list (above), 
# which cannot be changed, and a list of classes with same data (ELEMENTS) exist.
# The list 'ELEMENTS' can be modified by e.g. loading a separate custom
# data file.
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


# This function measures the distance between two selected objects.
def distance():

    # In the 'EDIT' mode
    if bpy.context.mode == 'EDIT_MESH':

        atom = bpy.context.edit_object
        bm = bmesh.from_edit_mesh(atom.data)
        locations = []

        for v in bm.verts:
            if v.select:
                locations.append(atom.matrix_world * v.co)
                
        if len(locations) > 1:
            location1 = locations[0]
            location2 = locations[1]        
        else:
            return "N.A"
    # In the 'OBJECT' mode
    else:

        if len(bpy.context.selected_bases) > 1:
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
                   who, 
                   radius_all, 
                   radius_pm, 
                   radius_type, 
                   radius_type_ionic,
                   sticks_all):

    # For selected objects of all selected layers
    if who == "ALL_IN_LAYER":
        # Determine all selected layers.
        layers = []
        for i, layer in enumerate(bpy.context.scene.layers):
            if layer == True:
                layers.append(i)
                
        # Put all objects, which are in the layers, into a list.
        change_objects_all = []
        for atom in bpy.context.scene.objects:
            for layer in layers:
                if atom.layers[layer] == True:
                    change_objects_all.append(atom)                                  
    # For selected objects of the visible layer                               
    elif who == "ALL_ACTIVE":
        change_objects_all = []
        # Note all selected objects first.
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
    if action_type == "ATOM_RADIUS_PM" and "Stick" not in atom.name:
        if radius_pm[0] in atom.name:
            atom.scale = (radius_pm[1]/100,) * 3
            
    # Modify atom radius (all selected)
    if action_type == "ATOM_RADIUS_ALL" and "Stick" not in atom.name:
        atom.scale *= radius_all      
              
    # Modify atom radius (type, van der Waals, atomic or ionic) 
    if action_type == "ATOM_RADIUS_TYPE" and "Stick" not in atom.name:
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
    if action_type == "STICKS_RADIUS_ALL" and ('Sticks_Cups' in atom.name or 
                                               'Sticks_Cylinder' in atom.name or
                                               'Stick_Cylinder' in atom.name):
    
        bpy.context.scene.objects.active = atom
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
        bpy.context.scene.objects.active = None

    # Replace atom objects
    if action_type == "ATOM_REPLACE_OBJ" and "Stick" not in atom.name:

        scn = bpy.context.scene.atom_blend
        
        new_material = draw_obj_material(scn.replace_objs_material, 
                                         atom.active_material)
        
        # Special object (like halo, etc.)
        if scn.replace_objs_special != '0':
            new_atom = draw_obj_special(scn.replace_objs_special, atom)
            new_atom.parent = atom.parent
        # Standard geomtrical objects    
        else:
            # If the atom shape shall not be changed, then:
            if scn.replace_objs == '0':
                atom.active_material = new_material 
                return {'FINISHED'}
            # If the atom shape shall change, then:
            else:
                new_atom = draw_obj(scn.replace_objs, atom)
                new_atom.active_material = new_material                
                new_atom.parent = atom.parent
                
                if "_repl" not in atom.name:
                    new_atom.name = atom.name + "_repl"
                else:
                    new_atom.name = atom.name 
                    
        # Delete the old object.
        bpy.ops.object.select_all(action='DESELECT')
        atom.select = True
        bpy.ops.object.delete()   
        del(atom)      

    # Default shapes and colors for atoms
    if action_type == "ATOM_DEFAULT_OBJ" and "Stick" not in atom.name:

        scn = bpy.context.scene.atom_blend     

        # Create new material
        new_material = bpy.data.materials.new("tmp")
        
        # Create new object (NURBS sphere = '1b')
        new_atom = draw_obj('1b', atom)
        new_atom.active_material = new_material
        new_atom.parent = atom.parent

        # Change size and color of the new object            
        for element in ELEMENTS:
            if element.name in atom.name:
                new_atom.scale = (element.radii[0],) * 3
                new_atom.active_material.diffuse_color = element.color
                new_atom.name = element.name

                name = atom.active_material.name
                if element.name+"_standard" in name:
                    pos = name.rfind("_standard")
                    if name[pos+9:].isdigit():
                        counter = int(name[pos+9:])
                        new_material.name = name[:pos]+"_standard"+str(counter+1)
                    else:
                        new_material.name = name+"_standard1"
                else:
                    new_material.name = name+"_standard1"
             
        # Finally, delete the old object
        bpy.ops.object.select_all(action='DESELECT')
        atom.select = True
        bpy.ops.object.delete()    


# Separating atoms from a dupliverts strucutre.
def separate_atoms(scn):

    atom = bpy.context.edit_object
        
    # Do nothing if it is not a dupliverts structure.
    if not atom.dupli_type == "VERTS":
       return {'FINISHED'}
        
    bm = bmesh.from_edit_mesh(atom.data)
    locations = []
    for v in bm.verts:
        if v.select:
            locations.append(atom.matrix_world * v.co)

    bm.free()
    del(bm)

    name  = atom.name
    scale = atom.children[0].scale
    material = atom.children[0].active_material

    # Separate the vertex from the main mesh and create a new mesh.
    bpy.ops.mesh.separate()
    new_object = bpy.context.scene.objects[0]
    # And now, switch to the OBJECT mode such that we can ...
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    # ... delete the new mesh including the separated vertex
    bpy.ops.object.select_all(action='DESELECT')
    new_object.select = True
    bpy.ops.object.delete()  

    # Create new atoms/vacancies at the position of the old atoms
    # For all selected positions do:
    for location in locations:
        # Create a new object by duplication of the child of the dupliverts
        # structure. <= this is done 'len(locations)' times. After each 
        # duplication, move the new object onto the positions
        bpy.ops.object.select_all(action='DESELECT')
        atom.children[0].select = True
        bpy.context.scene.objects.active = atom.children[0]
        bpy.ops.object.duplicate_move()
        new_atom = bpy.context.scene.objects.active
        new_atom.parent = None
        new_atom.location = location
        new_atom.name = atom.name + "_sep"    
        
    bpy.context.scene.objects.active = atom


# Prepare a new material
def draw_obj_material(material_type, material):

    if material_type == '0': # Unchanged
        material_new = material
    if material_type == '1': # Normal   
        material_new = bpy.data.materials.new(material.name + "_normal")
    if material_type == '2': # Transparent    
        material_new = bpy.data.materials.new(material.name + "_transparent")
        material_new.use_transparency = True        
        material_new.transparency_method = 'Z_TRANSPARENCY'
        material_new.alpha = 1.3
        material_new.raytrace_transparency.fresnel = 1.6
        material_new.raytrace_transparency.fresnel_factor = 1.6
    if material_type == '3': # Reflecting
        material_new = bpy.data.materials.new(material.name + "_reflecting")
        material_new.raytrace_mirror.use = True
        material_new.raytrace_mirror.reflect_factor = 0.6       
        material_new.raytrace_mirror.fresnel = 0.0
        material_new.raytrace_mirror.fresnel_factor = 1.250          
        material_new.raytrace_mirror.depth = 2
        material_new.raytrace_mirror.distance = 0.0        
        material_new.raytrace_mirror.gloss_factor = 1.0                   
    if material_type == '4': # Transparent + reflecting   
        material_new = bpy.data.materials.new(material.name + "_trans+refl")
        material_new.use_transparency = True
        material_new.transparency_method = 'Z_TRANSPARENCY'
        material_new.alpha = 1.3
        material_new.raytrace_transparency.fresnel = 1.6
        material_new.raytrace_transparency.fresnel_factor = 1.6
        material_new.raytrace_mirror.use = True
        material_new.raytrace_mirror.reflect_factor = 0.6       
        material_new.raytrace_mirror.fresnel = 0.0
        material_new.raytrace_mirror.fresnel_factor = 1.250          
        material_new.raytrace_mirror.depth = 2
        material_new.raytrace_mirror.distance = 0.0        
        material_new.raytrace_mirror.gloss_factor = 1.0 
        
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


# Draw an object (e.g. cube, sphere, cylinder, ...)
def draw_obj(atom_shape, atom):

    # No change
    if atom_shape == '0':
        return None

    current_layers=bpy.context.scene.layers

    if atom_shape == '1a': #Sphere mesh
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=32,
            ring_count=32,                    
            size=1, 
            view_align=False, 
            enter_editmode=False,
            location=atom.location,
            rotation=(0, 0, 0),
            layers=current_layers)
    if atom_shape == '1b': #Sphere NURBS
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(
            view_align=False, 
            enter_editmode=False,
            location=atom.location,
            rotation=(0.0, 0.0, 0.0),
            layers=current_layers)
    if atom_shape == '2': #Cube
        bpy.ops.mesh.primitive_cube_add(
            view_align=False, 
            enter_editmode=False,
            location=atom.location,
            rotation=(0.0, 0.0, 0.0),
            layers=current_layers)
    if atom_shape == '3': #Plane       
        bpy.ops.mesh.primitive_plane_add(
            view_align=False, 
            enter_editmode=False, 
            location=atom.location, 
            rotation=(0.0, 0.0, 0.0), 
            layers=current_layers)
    if atom_shape == '4a': #Circle
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, 
            radius=1, 
            fill_type='NOTHING', 
            view_align=False, 
            enter_editmode=False, 
            location=atom.location, 
            rotation=(0, 0, 0), 
            layers=current_layers)      
    if atom_shape == '4b': #Circle NURBS
        bpy.ops.surface.primitive_nurbs_surface_circle_add(
            view_align=False, 
            enter_editmode=False, 
            location=atom.location, 
            rotation=(0, 0, 0), 
            layers=current_layers)
    if atom_shape in {'5a','5b','5c','5d','5e'}: #Icosphere        
        index = {'5a':1,'5b':2,'5c':3,'5d':4,'5e':5}  
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=int(index[atom_shape]), 
            size=1, 
            view_align=False, 
            enter_editmode=False, 
            location=atom.location, 
            rotation=(0, 0, 0), 
            layers=current_layers)
    if atom_shape == '6a': #Cylinder
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=32, 
            radius=1, 
            depth=2, 
            end_fill_type='NGON', 
            view_align=False, 
            enter_editmode=False, 
            location=atom.location, 
            rotation=(0, 0, 0), 
            layers=current_layers)
    if atom_shape == '6b': #Cylinder NURBS
        bpy.ops.surface.primitive_nurbs_surface_cylinder_add(
            view_align=False, 
            enter_editmode=False, 
            location=atom.location, 
            rotation=(0, 0, 0), 
            layers=current_layers)          
    if atom_shape == '7': #Cone
        bpy.ops.mesh.primitive_cone_add(
            vertices=32, 
            radius1=1, 
            radius2=0, 
            depth=2, 
            end_fill_type='NGON', 
            view_align=False, 
            enter_editmode=False, 
            location=atom.location, 
            rotation=(0, 0, 0), 
            layers=current_layers)
    if atom_shape == '8a': #Torus
        bpy.ops.mesh.primitive_torus_add(
            rotation=(0, 0, 0), 
            location=atom.location, 
            view_align=False, 
            major_radius=1, 
            minor_radius=0.25, 
            major_segments=48, 
            minor_segments=12, 
            abso_major_rad=1, 
            abso_minor_rad=0.5)     
    if atom_shape == '8b': #Torus NURBS
        bpy.ops.surface.primitive_nurbs_surface_torus_add(
            view_align=False, 
            enter_editmode=False, 
            location=atom.location, 
            rotation=(0, 0, 0), 
            layers=current_layers)

    new_atom = bpy.context.scene.objects.active
    new_atom.scale = atom.scale + Vector((0.0,0.0,0.0))
    new_atom.name = atom.name + "_tmp"   
    new_atom.select = True
        
    return new_atom


# Draw a special object (e.g. halo, etc. ...)
def draw_obj_special(atom_shape, atom):

    current_layers=bpy.context.scene.layers

    # Halo cloud
    if atom_shape == '1':
        # Build one mesh point
        new_mesh = bpy.data.meshes.new("Mesh_"+atom.name)
        new_mesh.from_pydata([Vector((0.0,0.0,0.0))], [], [])
        new_mesh.update()
        new_atom = bpy.data.objects.new(atom.name + "_sep", new_mesh)
        bpy.context.scene.objects.link(new_atom)
        new_atom.location = atom.location
        material_new = bpy.data.materials.new(atom.active_material.name + "_sep")
        material_new.name = atom.name + "_halo"
        material_new.diffuse_color = atom.active_material.diffuse_color       
        material_new.type = 'HALO'
        material_new.halo.size = atom.scale[0]*1.5
        material_new.halo.hardness = 25
        material_new.halo.add = 0.0
        new_atom.active_material = material_new
        new_atom.name = atom.name
        new_atom.select = True
    # F2+ center
    if atom_shape == '2':
        # Create first a cube
        bpy.ops.mesh.primitive_cube_add(view_align=False, 
                                        enter_editmode=False,
                                        location=atom.location,
                                        rotation=(0.0, 0.0, 0.0),
                                        layers=current_layers)
        cube = bpy.context.scene.objects.active
        cube.scale = atom.scale + Vector((0.0,0.0,0.0))
        cube.name = atom.name + "_F2+-center"   
        cube.select = True                                        
        # New material for this cube
        material_cube = bpy.data.materials.new(atom.name + "_F2+-center")
        material_cube.diffuse_color = [0.8,0.0,0.0]     
        material_cube.use_transparency = True        
        material_cube.transparency_method = 'Z_TRANSPARENCY'
        material_cube.alpha = 1.0
        material_cube.raytrace_transparency.fresnel = 1.6
        material_cube.raytrace_transparency.fresnel_factor = 1.1
        cube.active_material = material_cube
        # Put a nice point lamp inside the defect
        lamp_data = bpy.data.lamps.new(name="F2+_lamp", type="POINT")
        lamp_data.distance = atom.scale[0] * 2.0
        lamp_data.energy = 20.0     
        lamp_data.use_sphere = True   
        lamp_data.color = [0.8,0.8,0.8]           
        lamp = bpy.data.objects.new("F2+_lamp", lamp_data)
        lamp.location = Vector((0.0, 0.0, 0.0))
        lamp.layers = current_layers
        bpy.context.scene.objects.link(lamp) 
        lamp.parent = cube
        # The new 'atom' is the F2+ defect 
        new_atom = cube        
    # F+ center
    if atom_shape == '3':
        # Create first a cube
        bpy.ops.mesh.primitive_cube_add(view_align=False, 
                                        enter_editmode=False,
                                        location=atom.location,
                                        rotation=(0.0, 0.0, 0.0),
                                        layers=current_layers)
        cube = bpy.context.scene.objects.active
        cube.scale = atom.scale + Vector((0.0,0.0,0.0))
        cube.name = atom.name + "_F+-center"   
        cube.select = True                                        
        # New material for this cube
        material_cube = bpy.data.materials.new(atom.name + "_F+-center")
        material_cube.diffuse_color = [0.8,0.8,0.0]     
        material_cube.use_transparency = True        
        material_cube.transparency_method = 'Z_TRANSPARENCY'
        material_cube.alpha = 1.0
        material_cube.raytrace_transparency.fresnel = 1.6
        material_cube.raytrace_transparency.fresnel_factor = 1.1
        cube.active_material = material_cube
        # Create now an electron
        scale = atom.scale / 10.0
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                                        view_align=False, 
                                        enter_editmode=False,
                                        location=(0.0, 0.0, 0.0),
                                        rotation=(0.0, 0.0, 0.0),
                                        layers=current_layers)     
        electron = bpy.context.scene.objects.active
        electron.scale = scale
        electron.name = atom.name + "_F+_electron"   
        electron.parent = cube 
        # New material for the electron
        material_electron = bpy.data.materials.new(atom.name + "_F+-center")
        material_electron.diffuse_color = [0.0,0.0,0.8]
        material_electron.specular_hardness = 200
        material_electron.emit = 1.0
        material_electron.use_transparency = True        
        material_electron.transparency_method = 'Z_TRANSPARENCY'
        material_electron.alpha = 1.3
        material_electron.raytrace_transparency.fresnel = 1.2
        material_electron.raytrace_transparency.fresnel_factor = 1.2
        electron.active_material = material_electron
        # Put a nice point lamp inside the electron
        lamp_data = bpy.data.lamps.new(name="F+_lamp", type="POINT")
        lamp_data.distance = atom.scale[0] * 2.0
        lamp_data.energy = 20.0     
        lamp_data.use_sphere = True   
        lamp_data.color = [0.8,0.8,0.8]           
        lamp = bpy.data.objects.new("F+_lamp", lamp_data)
        lamp.location = Vector((0.0, 0.0, 0.0))
        lamp.layers = current_layers
        bpy.context.scene.objects.link(lamp) 
        lamp.parent = cube
        # The new 'atom' is the F+ defect complex + lamp
        new_atom = cube
    # F0 center
    if atom_shape == '4':
        # Create first a cube
        bpy.ops.mesh.primitive_cube_add(view_align=False, 
                                        enter_editmode=False,
                                        location=atom.location,
                                        rotation=(0.0, 0.0, 0.0),
                                        layers=current_layers)
        cube = bpy.context.scene.objects.active
        cube.scale = atom.scale + Vector((0.0,0.0,0.0))
        cube.name = atom.name + "_F0-center"   
        cube.select = True                                        
        # New material for this cube
        material_cube = bpy.data.materials.new(atom.name + "_F0-center")
        material_cube.diffuse_color = [0.8,0.8,0.8]     
        material_cube.use_transparency = True        
        material_cube.transparency_method = 'Z_TRANSPARENCY'
        material_cube.alpha = 1.0
        material_cube.raytrace_transparency.fresnel = 1.6
        material_cube.raytrace_transparency.fresnel_factor = 1.1
        cube.active_material = material_cube
        # Create now two electrons
        scale = atom.scale / 10.0
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                                        view_align=False, 
                                        enter_editmode=False,
                                        location=(scale[0]*1.5,0.0,0.0),
                                        rotation=(0.0, 0.0, 0.0),
                                        layers=current_layers)     
        electron1 = bpy.context.scene.objects.active
        electron1.scale = scale
        electron1.name = atom.name + "_F0_electron1"   
        electron1.parent = cube 
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                                        view_align=False, 
                                        enter_editmode=False,
                                        location=(-scale[0]*1.5,0.0,0.0),
                                        rotation=(0.0, 0.0, 0.0),
                                        layers=current_layers)     
        electron2 = bpy.context.scene.objects.active
        electron2.scale = scale
        electron2.name = atom.name + "_F0_electron2"   
        electron2.parent = cube 
        # New material for the electrons
        material_electron = bpy.data.materials.new(atom.name + "_F0-center")
        material_electron.diffuse_color = [0.0,0.0,0.8]
        material_electron.specular_hardness = 200
        material_electron.emit = 1.0
        material_electron.use_transparency = True        
        material_electron.transparency_method = 'Z_TRANSPARENCY'
        material_electron.alpha = 1.3
        material_electron.raytrace_transparency.fresnel = 1.2
        material_electron.raytrace_transparency.fresnel_factor = 1.2
        electron1.active_material = material_electron
        electron2.active_material = material_electron
        # Put two nice point lamps inside the electrons
        lamp1_data = bpy.data.lamps.new(name="F0_lamp1", type="POINT")
        lamp1_data.distance = atom.scale[0] * 2.0
        lamp1_data.energy = 8.0     
        lamp1_data.use_sphere = True   
        lamp1_data.color = [0.8,0.8,0.8]           
        lamp1 = bpy.data.objects.new("F0_lamp", lamp1_data)
        lamp1.location = Vector((scale[0]*1.5, 0.0, 0.0))
        lamp1.layers = current_layers
        bpy.context.scene.objects.link(lamp1) 
        lamp1.parent = cube
        lamp2_data = bpy.data.lamps.new(name="F0_lamp2", type="POINT")
        lamp2_data.distance = atom.scale[0] * 2.0
        lamp2_data.energy = 8.0     
        lamp2_data.use_sphere = True   
        lamp2_data.color = [0.8,0.8,0.8]           
        lamp2 = bpy.data.objects.new("F0_lamp", lamp2_data)
        lamp2.location = Vector((-scale[0]*1.5, 0.0, 0.0))
        lamp2.layers = current_layers
        bpy.context.scene.objects.link(lamp2) 
        lamp2.parent = cube        
        # The new 'atom' is the F0 defect complex + lamps
        new_atom = cube
        
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
        
        li = ElementProp(item[0],item[1],item[2],item[3],
                                     radii,radii_ionic)
        ELEMENTS.append(li)


# Custom data file: changing color and radii by using the list 'ELEMENTS'.
def custom_datafile_change_atom_props():

    for atom in bpy.context.selected_objects:
        if len(atom.children) != 0:
            child = atom.children[0]
            if child.type in {'SURFACE', 'MESH', 'META'}:
                for element in ELEMENTS:
                    if element.name in atom.name:
                        child.scale = (element.radii[0],) * 3
                        child.active_material.diffuse_color = element.color
        else:
            if atom.type in {'SURFACE', 'MESH', 'META'}:
                for element in ELEMENTS:
                    if element.name in atom.name:
                        atom.scale = (element.radii[0],) * 3
                        atom.active_material.diffuse_color = element.color


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

        if "Atom" in line:

            line = data_file_p.readline()
            # Number
            line = data_file_p.readline()
            number = line[19:-1]
            # Name
            line = data_file_p.readline()
            name = line[19:-1]
            # Short name
            line = data_file_p.readline()
            short_name = line[19:-1]
            # Color
            line = data_file_p.readline()
            color_value = line[19:-1].split(',')
            color = [float(color_value[0]),
                     float(color_value[1]),
                     float(color_value[2])]
            # Used radius
            line = data_file_p.readline()
            radius_used = float(line[19:-1])
            # Atomic radius
            line = data_file_p.readline()
            radius_atomic = float(line[19:-1])
            # Van der Waals radius
            line = data_file_p.readline()
            radius_vdW = float(line[19:-1])
            radii = [radius_used,radius_atomic,radius_vdW]
            radii_ionic = []

            element = ElementProp(number,name,short_name,color,
                                              radii, radii_ionic)

            ELEMENTS.append(element)

    data_file_p.close()

    return True                           
