#!BPY

"""
Name: 'Paths (.svg, .ps, .eps, .ai, Gimp)'
Blender: 233
Group: 'Import'
Submenu: 'Gimp 1.0 - 1.2.5' Gimp_1_0
Submenu: 'Gimp 2.0' Gimp_2_0
Submenu: 'Illustrator (.ai) PS-Adobe-2.0' AI
Submenu: 'InkScape (.svg)' SVG
Submenu: 'Postscript (.eps/.ps) PS-Adobe-2.0' EPS
Tip: 'Import a path from any of a set of formats (still experimental)'
"""

__author__ = "Jean-Michel Soler (jms)"
__url__ = ("blender", "elysiun",
"AI importer's homepage, http://jmsoler.free.fr/didacticiel/blender/tutor/cpl_import_ai.htm",
"Communicate problems and errors, http://www.zoo-logique.org/3D.Blender/newsportal/thread.php?group=3D.Blender")
__version__ = "0.1.1"

__bpydoc__ = """\
Paths Import imports paths from a selection of different formats:

- Gimp 1.0 -> 1.2.5;<br>
- Gimp 2.0;<br>
- AI PS-Adobe 2.0;<br>
- Inkscape (svg);<br>
- Postscript (ps/eps)

Usage:
    Run the script from "File->Import", select the desired format from the
pop-up menu and select the file to open.

Notes:<br>
    If the imported curve looks "messy", you may need to enter edit mode with the imported curve selected and toggle cyclic mode for it, by selecting all its points and pressing "c" or using the Curve menu in the 3d view header.
"""

#----------------------------------------------
# (c) jm soler juillet 2004, released under Blender Artistic Licence 
#    for the Blender 2.34 Python Scripts Bundle.
#----------------------------------------------

import Blender

argv=__script__['arg']

if argv=='SVG':
  from svg2obj import *

elif argv=='AI':
  from ai2obj import *

elif argv=='EPS':
  from eps2obj import *

elif argv=='Gimp_1_0':
  from gimp2obj import *

elif argv=='Gimp_2_0':
  from svg2obj import *

text = 'Import %s' % argv
Blender.Window.FileSelector (fonctionSELECT, text)
