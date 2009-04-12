 # ***** BEGIN GPL LICENSE BLOCK *****
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
 # Contributor(s): Campbell Barton
 #
 # #**** END GPL LICENSE BLOCK #****

script_help_msg = '''
Usage,
run this script from blenders root path once you have compiled blender
	./blender.bin -P source/blender/python/epy_doc_gen.py

This will generate rna.py, generate html docs  by running...
	epydoc source/blender/python/doc/rna.py -o source/blender/python/doc/html -v --no-sourcecode  --no-sourcecode  --graph=classtree
	epydoc source/blender/python/doc/bpyoperator.py -o source/blender/python/doc/html -v --no-sourcecode  --no-sourcecode  --graph=classtree
'''

# if you dont have graphvis installed ommit the --graph arg.

def range_str(val):
	if val < -10000000:	return '-inf'
	if val >  10000000:	return 'inf'
	if type(val)==float:
		return '%g'  % val
	else:
		return str(val)	

def get_array_str(length):
	if length > 0:	return ' array of %d items' % length
	else:		return ''

def full_rna_struct_path(rna_struct):
	'''
	Needed when referencing one struct from another
	'''
	nested = rna_struct.nested
	if nested:
		return "%s.%s" % (full_rna_struct_path(nested), rna_struct.identifier)
	else:
		return rna_struct.identifier


def rna2epy(target_path):
	
	# Use for faster lookups
	# use rna_struct.identifier as the key for each dict
	rna_full_path_dict =	{}	# store the result of full_rna_struct_path(rna_struct)
	rna_children_dict =		{}	# store all rna_structs nested from here
	rna_references_dict =	{}	# store a list of rna path strings that reference this type
	rna_words = set()
	
	def write_struct(rna_struct, ident):
		identifier = rna_struct.identifier
		
		rna_base = rna_struct.base
		
		if rna_base:
			out.write(ident+ 'class %s(%s):\n' % (identifier, rna_base.identifier))
		else:
			out.write(ident+ 'class %s:\n' % identifier)
		
		out.write(ident+ '\t"""\n')
		
		title = 'The %s Object' % rna_struct.name
		description = rna_struct.description
		out.write(ident+ '\t%s\n' %  title)
		out.write(ident+ '\t%s\n' %  ('=' * len(title)))
		out.write(ident+ '\t\t%s\n' %  description)
		rna_words.update(description.split())
		
		
		# For convenience, give a list of all places were used.
		rna_refs= rna_references_dict[identifier]
		
		if rna_refs:
			out.write(ident+ '\t\t\n')
			out.write(ident+ '\t\tReferences\n')
			out.write(ident+ '\t\t==========\n')
			
			for rna_ref_string in rna_refs:
				out.write(ident+ '\t\t\t- L{%s}\n' % rna_ref_string)
			
			out.write(ident+ '\t\t\n')
		
		else:
			out.write(ident+ '\t\t\n')
			out.write(ident+ '\t\t(no references to this struct found)\n')
			out.write(ident+ '\t\t\n')
		
		for rna_prop_identifier, rna_prop in rna_struct.properties.items():
			
			if rna_prop_identifier=='RNA':
				continue
			
			if rna_prop_identifier=='rna_type':
				continue
			
			rna_desc = rna_prop.description
			
			if rna_desc: rna_words.update(rna_desc.split())
			if not rna_desc: rna_desc = rna_prop.name
			if not rna_desc: rna_desc = 'Note - No documentation for this property!'
			
			rna_prop_type = rna_prop.type.lower()
			
			if rna_prop_type=='collection':	collection_str = 'Collection of '
			else:							collection_str = ''
			
			try:		rna_prop_ptr = rna_prop.fixed_type
			except:	rna_prop_ptr = None
			
			try:		length = rna_prop.array_length
			except:	length = 0
			
			array_str = get_array_str(length)
			
			if rna_prop.editable:	readonly_str = ''
			else:				readonly_str = ' (readonly)'
			
			if rna_prop_ptr: # Use the pointer type
				out.write(ident+ '\t@ivar %s: %s\n' %  (rna_prop_identifier, rna_desc))
				out.write(ident+ '\t@type %s: %sL{%s}%s%s\n' %  (rna_prop_identifier, collection_str, rna_prop_ptr.identifier, array_str, readonly_str))
			else:
				if rna_prop_type == 'enum':
					out.write(ident+ '\t@ivar %s: %s in (%s)\n' %  (rna_prop_identifier, rna_desc, ', '.join(rna_prop.items.keys())))
					out.write(ident+ '\t@type %s: %s%s%s\n' %  (rna_prop_identifier, rna_prop_type,  array_str, readonly_str))
				elif rna_prop_type == 'int' or rna_prop_type == 'float':
					out.write(ident+ '\t@ivar %s: %s\n' %  (rna_prop_identifier, rna_desc))
					out.write(ident+ '\t@type %s: %s%s%s in [%s, %s]\n' %  (rna_prop_identifier, rna_prop_type, array_str, readonly_str, range_str(rna_prop.hard_min), range_str(rna_prop.hard_max) ))
				elif rna_prop_type == 'string':
					out.write(ident+ '\t@ivar %s: %s (maximum length of %s)\n' %  (rna_prop_identifier, rna_desc, rna_prop.max_length))
					out.write(ident+ '\t@type %s: %s%s%s\n' %  (rna_prop_identifier, rna_prop_type, array_str, readonly_str))
				else:
					out.write(ident+ '\t@ivar %s: %s\n' %  (rna_prop_identifier, rna_desc))
					out.write(ident+ '\t@type %s: %s%s%s\n' %  (rna_prop_identifier, rna_prop_type, array_str, readonly_str))
				
			
		out.write(ident+ '\t"""\n\n')
		
		# Now write children recursively
		for child in rna_children_dict[identifier]:
			write_struct(child, ident + '\t')
	
	out = open(target_path, 'w')

	def base_id(rna_struct):
		try:		return rna_struct.base.identifier
		except:	return '' # invalid id

	#structs = [(base_id(rna_struct), rna_struct.identifier, rna_struct) for rna_struct in bpy.doc.structs.values()]
	'''
	structs = []
	for rna_struct in bpy.doc.structs.values():
		structs.append( (base_id(rna_struct), rna_struct.identifier, rna_struct) )
	'''
	structs = []
	for rna_type_name in dir(bpy.types):
		rna_type = getattr(bpy.types, rna_type_name)
		if hasattr(rna_type, '__rna__'):
			#if not rna_type_name.startswith('__'):
			rna_struct = rna_type.__rna__
			identifier = rna_struct.identifier
			structs.append( (base_id(rna_struct), identifier, rna_struct) )	
			
			
			
			# Store full rna path 'GameObjectSettings' -> 'Object.GameObjectSettings'
			rna_full_path_dict[identifier] = full_rna_struct_path(rna_struct)
			
			# fill in these later
			rna_children_dict[identifier]= []
			rna_references_dict[identifier]= []
			
		else:
			print("Ignoring", rna_type_name)
	
	
	
	structs.sort() # not needed but speeds up sort below, setting items without an inheritance first
	
	# Arrange so classes are always defined in the correct order
	deps_ok = False
	while deps_ok == False:
		deps_ok = True
		rna_done = set()
		
		for i, (rna_base, identifier, rna_struct) in enumerate(structs):
			
			rna_done.add(identifier)
			
			if rna_base and rna_base not in rna_done:
				deps_ok = False
				data = structs.pop(i)
				ok = False
				while i < len(structs):
					if structs[i][1]==rna_base:
						structs.insert(i+1, data) # insert after the item we depend on.
						ok = True
						break
					i+=1
					
				if not ok:
					print('Dependancy "%s" could not be found for "%s"' % (identifier, rna_base))
				
				break
	
	# Done ordering structs
	
	
	# precalc vars to avoid a lot of looping
	for (rna_base, identifier, rna_struct) in structs:
		
		
		# rna_struct_path = full_rna_struct_path(rna_struct)
		rna_struct_path = rna_full_path_dict[identifier]
		
		for rna_prop_identifier, rna_prop in rna_struct.properties.items():
			if rna_prop_identifier=='RNA':
				continue
			
			if rna_prop_identifier=='rna_type':
				continue
			
			try:		rna_prop_ptr = rna_prop.fixed_type
			except:	rna_prop_ptr = None
			
			# Does this property point to me?
			if rna_prop_ptr:
				rna_references_dict[rna_prop_ptr.identifier].append( "%s.%s" % (rna_struct_path, rna_prop_identifier) )
		
		
		
		# Store nested children
		nested = rna_struct.nested
		if nested:
			rna_children_dict[nested.identifier].append(rna_struct)
	
	# Sort the refs, just reads nicer
	for rna_refs in rna_references_dict.values():
		rna_refs.sort()
	
	for (rna_base, identifier, rna_struct) in structs:
		if rna_struct.nested:
			continue
		
		write_struct(rna_struct, '')
		
		
	out.write('\n')
	out.close()
	
	# # We could also just run....
	# os.system('epydoc source/blender/python/doc/rna.py -o ./source/blender/python/doc/html -v')
	
	
	# Write graphviz
	out= open(target_path.replace('.py', '.dot'), 'w')
	out.write('digraph "rna data api" {\n')
	out.write('\tnode [style=filled, shape = "box"];\n')
	out.write('\toverlap=false;\n')
	out.write('\trankdir = LR;\n')
	out.write('\tsplines=true;\n')
	out.write('\tratio=auto;\n')
	
	
	
	out.write('\tsize="10,10"\n')
	#out.write('\tpage="8.5,11"\n')
	#out.write('\tcenter=""\n')
	
	def isop(rna_struct):
		return '_OT_' in rna_struct.identifier
	
	
	for (rna_base, identifier, rna_struct) in structs:
		if isop(rna_struct):
			continue
		
		base = rna_struct.base
		
		
		out.write('\t"%s";\n' % identifier)
	
	for (rna_base, identifier, rna_struct) in structs:
		
		if isop(rna_struct):
			continue
			
		base = rna_struct.base
		
		if base and not isop(base):
			out.write('\t"%s" -> "%s" [label="(base)" weight=1.0];\n' % (base.identifier, identifier))
		
		nested = rna_struct.nested
		if nested and not isop(nested):
			out.write('\t"%s" -> "%s" [label="(nested)"  weight=1.0];\n' % (nested.identifier, identifier))
		
		
		
		rna_refs= rna_references_dict[identifier]
		
		for rna_ref_string in rna_refs:
			
			if '_OT_' in rna_ref_string:
				continue
			
			ref = rna_ref_string.split('.')[-2]
			out.write('\t"%s" -> "%s" [label="%s" weight=0.01];\n' % (ref, identifier, rna_ref_string))
		
		
	
	out.write('}\n')
	out.close()
	
	# # We could also just run....
	# os.system('dot source/blender/python/doc/rna.dot -Tsvg -o ./source/blender/python/doc/rna.svg')
	
	
	out= open(target_path.replace('.py', '.words'), 'w')
	rna_words = list(rna_words)
	rna_words.sort()
	for w in rna_words:
		out.write('%s\n' % w)
	
	
	
	

def op2epy(target_path):
	out = open(target_path, 'w')
	
	operators = dir(bpy.ops)
	operators.remove('add')
	operators.remove('remove')
	operators.sort()
	
	for op in operators:
		
		if op.startswith('__'):
			continue
		
		# Keyword attributes
		kw_args = [] # "foo = 1", "bar=0.5", "spam='ENUM'"
		kw_arg_attrs = [] # "@type mode: int"
		
		# rna = getattr(bpy.types, op).__rna__
		rna = bpy.ops.__rna__(op)
		
		rna_struct = rna.rna_type
		# print (dir(rna))
		# print (dir(rna_struct))
		for rna_prop_identifier, rna_prop in rna_struct.properties.items():
			if rna_prop_identifier=='rna_type':
				continue
			# ['rna_type', 'name', 'array_length', 'description', 'hard_max', 'hard_min', 'identifier', 'precision', 'readonly', 'soft_max', 'soft_min', 'step', 'subtype', 'type']
			#rna_prop=  op_rna.rna_type.properties[attr]
			rna_prop_type = rna_prop.type.lower() # enum, float, int, boolean
			
			try:		length = rna_prop.array_length
			except:	length = 0
			
			array_str = get_array_str(length)
			
			try:
				val = getattr(rna, rna_prop_identifier)
				val_error = False
			except:
				val = "'<UNDEFINED>'"
				val_error = True
			
			kw_type_str= "@type %s: %s%s" % (rna_prop_identifier, rna_prop_type, array_str)
			kw_param_str= "@param %s: %s" % (rna_prop_identifier, rna_prop.description)
			kw_param_set = False
			
			if val_error:
				val_str = val
			elif rna_prop_type=='float':
				if length==0:
					val_str= '%g' % val
					if '.' not in val_str:
						val_str += '.0'
				else:
					# array
					val_str = str(tuple(val))
				
				kw_param_str += (' in (%s, %s)' % (range_str(rna_prop.hard_min), range_str(rna_prop.hard_max)))
				kw_param_set= True
				
			elif rna_prop_type=='int':
				if length==0:
					val_str='%d' % val
				else:
					val_str = str(tuple(val))
				
				# print(dir(rna_prop))
				kw_param_str += (' in (%s, %s)' % (range_str(rna_prop.hard_min), range_str(rna_prop.hard_max)))
				# These strings dont have a max length???
				#kw_param_str += ' (maximum length of %s)' %  (rna_prop.max_length)
				kw_param_set= True
				
			elif rna_prop_type=='boolean':
				if length==0:
					if val:	val_str='True'
					else:	val_str='False'
				else:
					val_str = str(tuple(val))
			
			elif rna_prop_type=='enum':
				# no array here?
				val_str="'%s'" % val
				kw_param_str += (' in (%s)' % ', '.join(rna_prop.items.keys()))
				kw_param_set= True
				
			elif rna_prop_type=='string':
				# no array here?
				val_str='"%s"' % val
			
			# todo - collection - array
			# print (rna_prop.type)
			
			kw_args.append('%s = %s' % (rna_prop_identifier, val_str))
			
			# stora 
			
			kw_arg_attrs.append(kw_type_str)
			if kw_param_set:
				kw_arg_attrs.append(kw_param_str)
			
		
		
		out.write('def %s(%s):\n' % (op, ', '.join(kw_args)))
		out.write('\t"""\n')
		out.write('\t%s\n' % rna_struct.description)
		for desc in kw_arg_attrs:
			out.write('\t%s\n' % desc)
		out.write('\t@rtype: None\n')
		out.write('\t"""\n')
	
	
	out.write('\n')
	out.close()

if __name__ == '__main__':
	if 'bpy' not in dir():
		print("\nError, this script must run from inside blender.")
		print(script_help_msg)
		
	else:
		rna2epy('source/blender/python/doc/rna.py')
		op2epy('source/blender/python/doc/bpyoperator.py')


	import sys
	sys.exit()
