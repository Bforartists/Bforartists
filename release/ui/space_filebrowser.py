
import bpy


class FILEBROWSER_HT_header(bpy.types.Header):
	__space_type__ = "FILE_BROWSER"

	def draw(self, context):
		st = context.space_data
		layout = self.layout
		
		params = st.params 
		layout.template_header()

		if context.area.show_menus:
			row = layout.row()
			row.itemM("FILEBROWSER_MT_directory")
			row.itemM("FILEBROWSER_MT_bookmarks")

		row = layout.row(align=True)
		row.itemO("file.parent", text="", icon='ICON_FILE_PARENT')
		row.itemO("file.refresh", text="", icon='ICON_FILE_REFRESH')
		row.itemO("file.previous", text="", icon='ICON_PREV_KEYFRAME')
		row.itemO("file.next", text="", icon='ICON_NEXT_KEYFRAME')
		
		layout.itemR(params, "display", expand=True, text="")
		layout.itemR(params, "sort", expand=True, text="")
		
		layout.itemR(params, "hide_dot")
		layout.itemR(params, "do_filter")
		
		row = layout.row(align=True)
		row.itemR(params, "filter_folder", text="");
		row.itemR(params, "filter_blender", text="");
		row.itemR(params, "filter_image", text="");
		row.itemR(params, "filter_movie", text="");
		row.itemR(params, "filter_script", text="");
		row.itemR(params, "filter_font", text="");
		row.itemR(params, "filter_sound", text="");
		row.itemR(params, "filter_text", text="");

		row.active = params.do_filter

class FILEBROWSER_MT_directory(bpy.types.Menu):
	__space_type__ = "FILE_BROWSER"
	__label__ = "Directory"

	def draw(self, context):
		layout = self.layout

		layout.itemO("file.directory_new", text="New Directory", icon='ICON_NEWFOLDER')
		layout.itemO("file.refresh", text="Refresh", icon='ICON_FILE_REFRESH')
		layout.itemO("file.parent", text="Parent", icon='ICON_FILE_PARENT')
		
class FILEBROWSER_MT_bookmarks(bpy.types.Menu):
	__space_type__ = "FILE_BROWSER"
	__label__ = "Bookmarks"

	def draw(self, context):
		layout = self.layout

		layout.itemO("file.add_bookmark", text="Add current directory", icon='ICON_BOOKMARKS')

		
bpy.types.register(FILEBROWSER_HT_header)
bpy.types.register(FILEBROWSER_MT_directory)
bpy.types.register(FILEBROWSER_MT_bookmarks)
