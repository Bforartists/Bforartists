#!BPY
""" Registration info for Blender menus: <- these words are ignored
Name: 'UV Copy from Active'
Blender: 242
Group: 'Object'
Tip: 'Copy UV coords from a mesh to another that has same vertex indices'
"""

__author__ = "Toni Alatalo, Martin Poirier et. al."
__url__ = ("blender", "elysiun",
"Script's homepage, http://www.elysiun.com/forum/viewtopic.php?t=14897", 
"Communicate problems and errors, http://www.elysiun.com/forum/viewtopic.php?t=14897")
__version__ = "0.2 01/2006"

__bpydoc__ = """\
This script copies UV coords from a mesh to another (version of the same mesh).
All target meshes must have the same number of faces at the active
"""

import Blender

def face_key(me):
	'''
	Returns the face lengths for this mesh
	only copy between meshes that have matching face_key's
	'''
	return tuple([len(f) for f in me.faces])

def main():
	scene = Blender.Scene.GetCurrent()

	source_ob = scene.objects.active
	
	if not source_ob or source_ob.type != 'Mesh':
		Blender.Draw.PupMenu("Error%t|No active object to copy UVs from.")
		return
	
	source_me = source_ob.getData(mesh=1)
	
	target_mes = [ ob.getData(mesh=1) for ob in scene.objects.context if ob != source_ob if ob.type == 'Mesh']
	
	# remove double meshes
	target_mes = dict([(me.name, me) for me in target_mes])
	target_mes = target_mes.values()
	
	if not target_mes:
		Blender.Draw.PupMenu("Error%t|No selected object(s) to copy UVs to.")
		return
	
	source_me = source_ob.getData(mesh=1)
	
	if not source_me.faceUV:
		Blender.Draw.PupMenu("Error%t|Active mesh has no UVs.")
		return
	
	if not target_mes:
		Blender.Draw.PupMenu("Error%t|no selected object other than the source, hence no target defined.")
		return
	error = False
	
	source_face_key = face_key(source_me)
	source_faces = source_me.faces
	
	fail_count = 0
	
	for target in target_mes:
		if len(source_me.faces) != len(target.faces):
			print '\ttarget "%s" facelen does not match "%s".' % (target.name, source_me.name)
			error = True
			fail_count +=1
		else:
			# slow but worth comparing
			if source_face_key != face_key(target):
				print '\t\terror, face len dosnt match for ob "%s" next mesh...' % target.name
				error = True
				fail_count +=1
			else:
				target_faces = target.faces
				
				# Add uvs if there not there
				target.faceUV = True
				
				for i, f_source in enumerate(source_faces): 
					target_faces[i].uv = f_source.uv
				
				target.update()
	
	msg = 'Copied UVs to %d of %d mesh(s)' % (len(target_mes)-fail_count, len(target_mes))
	
	if error:
		msg += "|Could not copy some UV's, see console."
	
	Blender.Draw.PupMenu('UV Copy Finished%t|' + msg)

if __name__ == '__main__':
	main()