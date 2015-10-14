Geodesic_Domes
Based on a script by Andy Houston (serendipiti) for Blender 2.49
Original Script Documentation:
http://wiki.blender.org/index.php/Extensions:2.4/Py/Scripts/Wizards/Geodesic_dome
Licence:
GPL

Previous conveersion to 2.50 by PKHG (latest notes after PKHG's)
BIG change after revision 2551 GUI adjusted ...
You should download anew if older then 24-november-2011

In principle all parts work:
the *hedrons with superformparameters
Grid ... Sphere with superformparameters
Faces  **
Hubs   **
Struts **

** means will be adjusted ... at the moment you  have to name objects and
execute eventually again ;-( ...

but PKHG is content with a this nearly 95% converted version.

TODO, ranges of parameters could be chosen differently. Inform PKHG!

Uplaod will be done today (25-11 at about 19.30... GMT -+1)

_259 in the names is not important ... but let it be so (now) ;-)

Converted by Harry Ayres (Noctumsolis)
20-May-2014: v0.3.1 for Blender 2.70

Minor API fixes:
  * Module names updated.
  * Function calls updated.
Minor Python fix:
  * str(type()) double-cast to match string literal replaced with isinstance.
  
No other updates yet. Possibly in the future.

15-July-2014 V0.3.2 for Blender 2.71
PKHG 17jul14 Hubs and Strubs need adjustement in 2.71
(Struts half done?!11:00) 
seems to be ok now

PKHG TODO understand the shapkey files and implement?!
