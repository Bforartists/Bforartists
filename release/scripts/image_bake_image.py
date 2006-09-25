#!BPY
"""
Name: 'Bake Texface Image from UVs'
Blender: 242
Group: 'Image'
Tooltip: 'Make a new image from the texface of the selected mesh objects.'
"""
__author__= ['Campbell Barton']
__url__= ('blender', 'elysiun', 'http://www.gametutorials.com')
__version__= '0.1'
__bpydoc__= '''\
Bake Texface Images to 1 image

This script makes an image from a meshes texface images, using the UV coordinates
to draw the faces into the image.

This makes it possible to bake many images into 1 texture.

Make sure your UV Coordinates do not overlap.
LSCM Unwrapper or archimap unwrapper work well to automaticaly do this.
'''

import Blender
import BPyRender
#reload(BPyRender)
import BPyMessages
Vector= Blender.Mathutils.Vector
Create= Blender.Draw.Create


def main():
	# Create the variables.
	# Filename without path or extension.
	# Big LC, gets all unique mesh objects from the selection that have UV coords.
	me_s= dict([\
	  (ob.getData(name_only=1), ob.getData(mesh=1))\
	  for ob in Blender.Object.GetSelected()\
	  if ob.getType()=='Mesh'  if ob.getData(mesh=1).faceUV]).values()
	
	if not me_s:
		BPyMessages.Error_NoMeshUvSelected()
		return
		
	newpath= Blender.Get('filename').split('/')[-1].split('\\')[-1].replace('.blend', '_img.png')
	###PREF_IMAGE_PATH = Create('//%s_img' % newpath)
	PREF_IMAGE_SIZE = Create(512)
	PREF_IMAGE_BLEED = Create(4)
	PREF_IMAGE_SMOOTH= Create(0)
	
	PREF_SEL_FACES_ONLY= Create(0)
	
	pup_block = [\
	###('', PREF_IMAGE_PATH, 3, 100, 'Path to new Image. "//" for curent blend dir.'),\
	('Pixel Size:', PREF_IMAGE_SIZE, 64, 4096, 'Image Width and Height.'),\
	('Pixel Bleed:', PREF_IMAGE_BLEED, 0, 64, 'Extend pixels from boundry edges to avoid mipmapping errors on rendering.'),\
	('Smooth lines', PREF_IMAGE_SMOOTH, 'Render smooth lines.'),\
	'',\
	('Selected Faces only', PREF_SEL_FACES_ONLY, 'Only bake from selected faces.'),\
	]
	
	if not Blender.Draw.PupBlock('Texface Image Bake', pup_block):
		return
	
	
	# Defaults for VCol, user cant change
	PREF_IMAGE_WIRE= False
	PREF_IMAGE_WIRE_INVERT= False
	PREF_IMAGE_WIRE_UNDERLAY= False
	
	PREF_USE_IMAGE= True # of course we need this one 
	
	PREF_USE_VCOL= False
	PREF_USE_MATCOL= False
	PREF_USE_NORMAL= False
	PREF_USE_TEXTURE= False
	
	def file_sel(PREF_IMAGE_PATH):
		
		if not (BPyMessages.Warning_SaveOver(PREF_IMAGE_PATH) and \
		BPyMessages.Warning_SaveOver(PREF_IMAGE_PATH+'.png')):
			return
		
		image = BPyRender.vcol2image(me_s,\
		PREF_IMAGE_PATH,\
		PREF_IMAGE_SIZE.val,\
		PREF_IMAGE_BLEED.val,\
		PREF_IMAGE_SMOOTH.val,\
		PREF_IMAGE_WIRE,\
		PREF_IMAGE_WIRE_INVERT,\
		PREF_IMAGE_WIRE_UNDERLAY,\
		PREF_USE_IMAGE,\
		PREF_USE_VCOL,\
		PREF_USE_MATCOL,\
		PREF_USE_NORMAL,\
		PREF_USE_TEXTURE,\
		PREF_SEL_FACES_ONLY.val)
		
		if image:
			image.makeCurrent()
		
		Blender.Window.RedrawAll()
	
	Blender.Window.FileSelector(file_sel, 'SAVE PNG', newpath)

if __name__ == '__main__':
	main()
