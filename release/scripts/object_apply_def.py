#!BPY

"""
Name: 'Apply Deformation'
Blender: 242
Group: 'Object'
Tooltip: 'Make copys of all the selected objects with modifiers, softbodies and fluid baked into a mesh'
""" 

__author__ = "Martin Poirier (theeth), Jean-Michel Soler (jms), Campbell Barton (ideasman)"
# This script is the result of merging the functionalities of two other:
# Martin Poirier's Apply_Def.py and
# Jean-Michel Soler's Fix From Everything

__url__ = ("http://www.blender.org", "http://blenderartists.org", "http://members.iinet.net.au/~cpbarton/ideasman/", "http://jmsoler.free.fr")
__version__ = "1.6 07/07/2006"

__bpydoc__ = """\
This script creates "raw" copies of deformed meshes.

Usage:

Select any number of Objects and run this script.  A fixed copy of each selected object
will be created, with the word "_def" appended to its name. If an object with
the same name already exists, it appends a number at the end as Blender itself does.

Objects in Blender can be deformed by armatures, lattices, curve objects and subdivision,
but this will only change its appearance on screen and rendered
images -- the actual mesh data is still simpler, with vertices in an original
"rest" position and less vertices than the subdivided version.

Use this script if you want a "real" version of the deformed mesh, so you can
directly manipulate or export its data.

This script will work with object types: Mesh, Metaballs, Text3d, Curves and Nurbs Surface.
"""


# $Id$
#
# --------------------------------------------------------------------------
# ***** BEGIN GPL LICENSE BLOCK *****
#
# Copyright (C) 2003: Martin Poirier, theeth@yahoo.com
#
# Thanks to Jonathan Hudson for help with the vertex groups part
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****


import Blender
import BPyMesh


def mesh_from_ob(ob):
	'''
	This wraps 
	BPyMesh.getMeshFromObject
	and NMesh.GetRawFromObject()
	
	Because BPyMesh.getMeshFromObject dosent do softbody meshes at the moment - a problem with Mesh
	
	WARNING Returns a Mesh or NMesh, should be ok- but take care
	'''
	if ob.isSB():
		# NMesh for softbody
		try:
			return Blender.NMesh.GetRawFromObject(ob.name)
		except:
			return None
	else:
		# Mesh for no softbody
		return BPyMesh.getMeshFromObject(ob, vgroups=False)



def apply_deform():
	scn= Blender.Scene.GetCurrent()
	ADD= Blender.Mesh.AssignModes.ADD
	#Blender.Window.EditMode(0)
	
	NAME_LENGTH = 19
	PREFIX = "_def"
	PREFIX_LENGTH = len(PREFIX)
	# Get all object and mesh names
	

	ob_list = Blender.Object.GetSelected()
	
	# Assume no soft body
	has_sb= False
	
	# reverse loop so we can remove objects (metaballs in this case)
	for ob_idx in xrange(len(ob_list)-1, -1, -1):
		ob= ob_list[ob_idx]
		
		ob.sel = 0 # deselect while where checking the metaballs
		
		# Test for a softbody
		if not has_sb and ob.isSB():
			has_sb= True
		
		# Remove all numbered metaballs because their disp list is only on the main metaball (un numbered)
		if ob.getType()=='MBall':
			name= ob.name
			# is this metaball numbered?
			dot_idx= name.rfind('.') + 1
			if name[dot_idx:].isdigit():
				# Not the motherball, ignore it.
				del ob_list[ob_idx]
			
	
	if not ob_list:
		Blender.Draw.PupMenu('No objects selected, nothing to do.')
		return
	
	
	if has_sb:
		curframe=Blender.Get('curframe')
		for f in xrange(curframe):
			Blender.Set('curframe',f+1)
			Blender.Window.RedrawAll()

	used_names = [ob.name for ob in Blender.Object.Get()]
	used_names.extend(Blender.NMesh.GetNames())
	
	
	deformedList = []
	for ob in ob_list:
		
		# Get the mesh data
		new_me= mesh_from_ob(ob)
		if not new_me:
			continue # Object has no display list
		
		
		name = ob.name
		new_name = "%s_def" % name[:NAME_LENGTH-PREFIX_LENGTH]
		num = 0
		
		while new_name in used_names:
			new_name = "%s_def.%.3i" % (name[:NAME_LENGTH-(PREFIX_LENGTH+PREFIX_LENGTH)], num)
			num += 1
		used_names.append(new_name)
		

			
		new_me.name= new_name
		
		new_ob= Blender.Object.New('Mesh', new_name)
		new_ob.link(new_me)
		scn.link(new_ob)
		new_ob.setMatrix(ob.matrixWorld)
		new_ob.Layers= ob.Layers
		
		deformedList.append(new_ob)
		
		# Original object was a mesh? see if we can copy any vert groups.
		if ob.getType()=='Mesh':
			orig_me= ob.getData(mesh=1)
			
			vgroups= orig_me.getVertGroupNames()
			if vgroups:
				new_me= new_ob.getData(mesh=1) # Do this so we can de vgroup stuff
				for vgroupname in vgroups:
					new_me.addVertGroup(vgroupname)
					if len(new_me.verts) == len(orig_me.verts):
						vlist = orig_me.getVertsFromGroup(vgroupname, True)
						try:
							for vpair in vlist:
								new_me.assignVertsToGroup(vgroupname, [vpair[0]], vpair[1], ADD)
						except:
							pass
	
	for ob in deformedList:
		ob.sel = 1
	
	if deformedList:
		deformedList[0].sel = 1 # Keep the same object active.
		
	Blender.Window.RedrawAll()

if __name__=='__main__':
	apply_deform()