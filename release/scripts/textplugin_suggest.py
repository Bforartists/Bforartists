#!BPY
"""
Name: 'Suggest All'
Blender: 246
Group: 'TextPlugin'
Shortcut: 'Ctrl+Space'
Tooltip: 'Performs suggestions based on the context of the cursor'
"""

# Only run if we have the required modules
try:
	import bpy
	from BPyTextPlugin import *
	OK = True
except ImportError:
	OK = False

def check_membersuggest(line, c):
	pos = line.rfind('.', 0, c)
	if pos == -1:
		return False
	for s in line[pos+1:c]:
		if not s.isalnum() and not s == '_':
			return False
	return True

def check_imports(line, c):
	if line.rfind('import ', 0, c) == c-7:
		return True
	if line.rfind('from ', 0, c) == c-5:
		return True
	return False

def main():
	txt = bpy.data.texts.active
	(line, c) = current_line(txt)
	
	# Check we are in a normal context
	if get_context(txt) != NORMAL:
		return
	
	# Check the character preceding the cursor and execute the corresponding script
	
	if check_membersuggest(line, c):
		import textplugin_membersuggest
		return
	
	elif check_imports(line, c):
		import textplugin_imports
		return
	
	# Otherwise we suggest globals, keywords, etc.
	list = []
	pre = get_targets(line, c)
	
	for k in KEYWORDS:
		list.append((k, 'k'))
	
	for k, v in get_builtins().items():
		list.append((k, type_char(v)))
	
	for k, v in get_imports(txt).items():
		list.append((k, type_char(v)))
	
	for k, v in get_defs(txt).items():
		list.append((k, 'f'))
	
	for k in get_vars(txt):
		list.append((k, 'v'))
	
	list.sort(cmp = suggest_cmp)
	txt.suggest(list, pre[-1])

if OK:
	main()
