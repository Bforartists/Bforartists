Blender CAD utils (for Blender 2.80+)
=====================================

A tiny subset of unmissable CAD functions for Blender 3d.  
Addon [page on blender.org/wiki](http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Modeling/mesh_tinyCAD) (Which has most of the same info]  

### Installation

The add-on is currently included in standard installations on Blender 2.78 onwards. Enable it by doing a search in `User Preferences > Add-ons > and type 'tiny' into the search field`. Enable 'Mesh: tinyCAD Mesh tools'.

In Blender 2.80 distributions you might encounter an older version of this add-on, if it fails to load/run/enable, please install it again from this github repository. 

__________________


### OK, what's this all about?

Dedicated CAD software speeds up drafting significantly with functions like: `Extend`, `Trim`,  `Intersect`, `Fillet /w radius` and `Offset /w distance`. At the moment of this writing many of these functions aren't included by default in regular distributions on Blender.org, so i've coded scripts to perform a few of the main features that I missed most. 
  
My scripts have shortnames: `VTX, V2X, XALL, BIX, CCEN` and are described separately in sections below. `Fillet` and `Offset` are written by zmj100 and can be found [here](http://blenderartists.org/forum/showthread.php?179375).


Since I started this repository: Vertex Fillet / Bevel was added to master. So no more need for a separate addon.  (Ctrl+Shift+b)

### VTX

The VTX script has lived in contrib distributions of Blender since 2010, with relatively minor changes. The feedback from BlenderArtists has been [overwhelmingly positive](http://blenderartists.org/forum/showthread.php?204836-CAD-Addon-Edge-Tools-(blender-2-6x)). I'm not going to claim it's bug free, but finding any showstopping issues has proven difficult. It now performs V, T or X selection automatically.   
  
Expect full freedom of orientation, but stuff must really intersect within error margins (`1.5E-6` = tolerance). These kinds of functions are handy for drawing construction lines and fixing up geometry. 

  - V : extending two edges towards their _calculated_ intersection point.  
   ![V](http://i.imgur.com/zBSciFf.png)

  - T : extending the path of one edge towards another edge.  
   ![T](http://i.imgur.com/CDH5oHm.png)

  - X : two edges intersect, their intersection gets a weld vertex. You now have 4 edges and 5 vertices.  
   ![X](http://i.imgur.com/kqtX9OE.png)


- Select two edges  
- hit `Spacebar` and type `vtx` ..select `autoVTX`  
- Bam. the rest is taken care of.


### X ALL

Intersect all, it programatically goes through all selected edges and slices them all using any found intersections, then welds them.

  - XALL is fast!  
  ![Imgur](http://i.imgur.com/1I7totI.gif)
  - Select as many edges as you want to intersect.
  - hit `spacebar` and type `xa`  ..select `XALL intersect all edges`

### V2X (Vertex to Intersection)

This might be a niche accessory, but sometimes all you want is a vertex positioned on the intersection of two edges. Nothing fancy.

### BIX (generate Bisector)

Creates a single edge which is the bisect of two edges.  
![Imgur](http://i.imgur.com/uzyv1Mv.gif)  

### CCEN (Circle Centers)

Given either 

- two adjacent edges on the circumference of an incomplete circle
- or three vertices (not required to be adjacent)

this operator will places the 3d cursor at original center of that circle.

![imgur](https://cloud.githubusercontent.com/assets/619340/5595657/2786f984-9279-11e4-9dff-9db5d5a52a52.gif)

updated version may become a modal operator to generate a full set of circle vertices, with variable vertex count.

![imgur demo](https://cloud.githubusercontent.com/assets/619340/5602194/ce613c96-933d-11e4-9879-d2cfc686cb69.gif)
  
### E2F (Extend Edge to Selected Face, Edge 2 Face)

Select a single Edge and a single Polygon (ngon, tri, quad) within the same Object. Execute `W > TinyCAD > E2F`

![image](https://cloud.githubusercontent.com/assets/619340/12091278/2884820e-b2f6-11e5-9f1b-37ebfdf10cfc.png)


### Why on github?

The issue tracker, use it.  

-  Let me know if these things are broken in new releases. Why? I don't update Blender as often as some so am oblivious to the slow evolution. 
-  If you can make a valid argument for extra functionality and it seems like something I might use or be able to implement for fun, it's going to happen.
-  I'm always open to pull requests (just don't expect instant approval of something massive, we can talk..you can use your gift of persuasion and sharp objectivism)
