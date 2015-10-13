# ***** BEGIN GPL LICENSE BLOCK *****
#
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
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Intellisense for Text Editor",
    "author": "Mackraken",
    "version": (0, 2),
    "blender": (2, 60, 0),
    "location": "Ctrl + Space at Text Editor",
    "description": "Adds intellense to the Text Editor",
    "warning": "Only works with 2.57 intellisense",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"}

import bpy

def complete(context):
	from console import intellisense
	from console_python import get_console

	sc = context.space_data
	text = sc.text

	region = context.region
	for area in context.screen.areas:
		if area.type=="CONSOLE":
			region = area.regions[1]
			break

	console = get_console(hash(region))[0]

	line = text.current_line.body
	cursor = text.current_character

	result  = intellisense.expand(line, cursor, console.locals, bpy.app.debug)

	return result


class Intellimenu(bpy.types.Menu):
	bl_label = ""
	bl_idname = "IntelliMenu"

	text = ""

	def draw(self, context):
		layout = self.layout
		#Very ugly see how can i fix this
		options = complete(context)

		options = options[2].split("  ")
		for op in options:
			layout.operator("text.intellioptions", text=op).text=op

#This operator executes when hits Ctrl+Space at the text editor

class Intellisense(bpy.types.Operator):
	#"""Tooltip"""
	bl_idname = "text.intellisense"
	bl_label = "Text Editor Intellisense"

	text = ""

#	@classmethod
#	def poll(cls, context):
#		return context.active_object is not None

	def execute(self, context):
		sc = context.space_data
		text = sc.text

		if text.current_character>0:
			result = complete(context)

			#print(result)

			if result[2]=="":
				text.current_line.body = result[0]
				bpy.ops.text.move(type='LINE_END')
			else:
				bpy.ops.wm.call_menu(name=Intellimenu.bl_idname)

		return {'FINISHED'}

#this operator completes the line with the options you choose from the menu
class Intellioptions(bpy.types.Operator):
	#"""Tooltip"""
	bl_idname = "text.intellioptions"
	bl_label = "Intellisense options"

	text = bpy.props.StringProperty()

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):
		sc = context.space_data
		text = sc.text

		comp = self.text
		line = text.current_line.body

		lline = len(line)
		lcomp = len(comp)

		#intersect text
		intersect = [-1,-1]

		for i in range(lcomp):
			val1 = comp[0:i+1]

			for j in range(lline):
				val2 = line[lline-j-1::]
				#print("	",j, val2)

				if val1==val2:
					intersect = [i, j]
					break

		if intersect[0]>-1:
			newline = line[0:lline-intersect[1]-1]+comp
		else:
			newline = line + comp

		#print(newline)
		text.current_line.body = newline

		bpy.ops.text.move(type='LINE_END')


		return {'FINISHED'}

def send_console(context, all=0):

	sc = context.space_data
	text = sc.text

	console = None

	for area in bpy.context.screen.areas:
		if area.type=="CONSOLE":
			from console_python import get_console

			console = get_console(hash(area.regions[1]))[0]

	if console==None:
		return {'FINISHED'}

	if all:

		for l in text.lines:
			console.push(l.body)

	else:
		#print(console.prompt)
		console.push(text.current_line.body)




class TestLine(bpy.types.Operator):
	#"""Tooltip"""
	bl_idname = "text.test_line"
	bl_label = "Test line"

	all = bpy.props.BoolProperty(default=False)


#   @classmethod
#   def poll(cls, context):
#	   return context.active_object is not None

	def execute(self, context):
		#print("test line")

		#send_console(context, self.all)
		sc = context.space_data
		text = sc.text

		line = text.current_line.body
		console = None

		for area in bpy.context.screen.areas:
			if area.type=="CONSOLE":
				from console_python import get_console

				console = get_console(hash(area.regions[1]))[0]

		if console==None:
			return {'FINISHED'}

		command = ""

		forindex = line.find("for ")
		if forindex >-1:

			var = line[forindex+4:-1]
			var = var[0:var.find(" ")]
			state = line[line.rindex(" ")+1:-1]

			command = var + " = " +state+"[0]"


		else:
			command = line

		#print(command)
		try:
			console.push(command)
		except:
			pass

		bpy.ops.text.line_break()


		return {'FINISHED'}
class SetBreakPoint(bpy.types.Operator):
	bl_idname = "text.set_breakpoint"
	bl_label = "Set Breakpoint"

	def execute(self, context):

		sc = bpy.context.space_data
		text = sc.text

		line = text.current_line
		br = " #breakpoint"
		#print(line.body.find(br))
		if line.body.find(br)>-1:

			line.body = line.body.replace(br, "")
		else:

			line.body += br

		return {'FINISHED'}

class Debug(bpy.types.Operator):
	bl_idname = "text.debug"
	bl_label = "Debug"

	def execute(self, context):

		binpath = bpy.app.binary_path

		addonspath = binpath[0:binpath.rindex("\\")+1]+str(bpy.app.version[0])+"."+str(bpy.app.version[1])+"\\scripts\\addons\\"

		print(addonspath)

		sc = context.space_data
		text = sc.text

		br = " #breakpoint"

		filepath = addonspath+"debug.py"
		file = open(filepath, "w")
		file.write("import pdb\n")

		for line in text.lines:
			l = line.body

			if line.body.find(br)>-1:
				indent = ""
				for letter in line.body:

					if not letter.isalpha():
						indent+=letter
					else:
						break
				file.write(l[0:-len(br)]+"\n")

				file.write(indent+"pdb.set_trace()\n")

			else:
				file.write(line.body+"\n")



		file.close()

		import pdb
		import debug

		pdb.runcall("debug")


		return {'FINISHED'}


class DebugPanel(bpy.types.Panel):
	bl_label = "Debug"
	bl_idname = "text.test_line"
	bl_space_type = "TEXT_EDITOR"
	bl_region_type = "UI"
	#bl_context = "object"

	text = bpy.props.StringProperty()

	def draw(self, context):
		layout = self.layout
		row = layout.row()

		text = self.text
		row = layout.row()
		row.operator("text.debug", text ="Debug")
		row = layout.row()
		row.operator("text.set_breakpoint")
		row = layout.row()
		row.operator("text.test_line").all=False
		row = layout.row()
		row.operator("text.test_line", text ="Test All").all=True

		row = layout.row()
		row.label(text="Coming Soon ...")


### ASSIGN A KEY

#section = Input section. "Window, Text, ..."
#name = operator name or wm.call_menu
#type = key
#event = keyboard event (Press, release, ...)
#mods = array containing key modifiers (["ctrl", "alt", "shift"]
#propvalue = menu name, if name is set to "wm.call_menu"
#overwrite doesnt work at the moment

def assignKey(section, name, type, event, mods=[],propvalue = "",  overwrite=0):

	kconf = bpy.context.window_manager.keyconfigs.active


	#check section
	validsections = [item.name for item in kconf.keymaps]
	if not section in validsections:
		print(section  + " is not a valid section.")
		#print(validsections)
		return False

	#check type
	type = type.upper()
	validkeys = [item.identifier for item in bpy.types.KeyMapItem.bl_rna.properties['type'].enum_items]
	if not type in validkeys:
		print(type + " is not a valid key.")
		#print(validkeys)
		return False


	#check event
	event = event.upper()
	validevents = [item.identifier for item in bpy.types.KeyMapItem.bl_rna.properties['value'].enum_items]
	if not event in validevents:
		print(event + " is not a valid event.")
		#print(validevents)

	kmap = kconf.keymaps[section]


#   get mods
	for i, mod in enumerate(mods):
		mods[i]= mod.lower()

	#any, shift, ctrl, alt, oskey
	kmod = [False, False, False, False, False]

	if "any" in mods: kmod[0] = True
	if "shift" in mods: kmod[1] = True
	if "ctrl" in mods: kmod[2] = True
	if "alt" in mods: kmod[3] = True
	if "oskey" in mods: kmod[4] = True

#   #check if key exist
	kexists = False

	for key in kmap.keymap_items:
		keymods = [key.any, key.shift, key.ctrl, key.alt, key.oskey]
		if key.type == type and keymods == kmod:
			kexists = True
			print(key,"key exists")
			break

	if kexists:
		#overwrite?
		if overwrite:
			key.idname=name

			#key.type = type

	else:
		#create key
		key = kmap.keymap_items.new(name, type, event, False)
		key.any = kmod[0]
		key.shift = kmod[1]
		key.ctrl = kmod[2]
		key.alt = kmod[3]
		key.oskey = kmod[4]

		if propvalue!="": key.properties.name = propvalue




classes = [Intellisense, Intellioptions, Intellimenu, DebugPanel, TestLine, SetBreakPoint, Debug]

def register():

	for c in classes:
		bpy.utils.register_class(c)

	assignKey("Text", "text.intellisense", "SPACE", "Press",  ["ctrl"])
	assignKey("Text", "text.test_line", "RET", "Press", [],"",1)

def unregister():
	for c in classes:
		bpy.utils.unregister_class(c)

if __name__ == "__main__":
	register()
