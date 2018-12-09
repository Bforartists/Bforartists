# Copyright 2015 Théo Friberg under GNU GPL 3

bl_info = {
	"name": "Cycles Automatic Materials",
	"author": "Théo Friberg",
	"blender": (2, 70, 0),
	"version": (0, 39),
	"location": "Space > Automatic / Adjustable Material from Image",
	"description": "One-click material setup from texture for Cycles. Blur from b°wide node pack.",
	"warning": "Still a work in progress",
	"wiki_url": "",
	"tracker_url": "mailto:theo.friberg@gmail.com?subject="
	"Bug report for Cycles Automatic Materials addon&body="
	"I have come across the following error while using the Cycles automatic"
	" materials addon (Please explain both the symptoms of the error and"
	" what you were doing when the error occured. If you think a specific"
	" action of yours is related to the error, please include a description"
	" of it too.):",
	"support": "COMMUNITY",
	"category": "Render"}

if "bpy" in locals():
	import importlib
	importlib.reload(JSONOps)
	importlib.reload(AutoOp)
	importlib.reload(AdjOp)

else:
	from . import JSONOps
	from . import AutoOp
	from . import AdjOp


import bpy
import json
import os

def menu_draw(self, context):
    self.layout.operator("com.new_automat", text="Automatic Material from Image", icon="FILE_IMAGE")


def register():

	"""This method registers the AutomatOperatorFromTexture
operator  and the AdjustableOperatorFromTexture operator.  """

	bpy.utils.register_class(AutoOp.AutomatOperatorFromTexture)
	bpy.utils.register_class(AdjOp.AdjustableOperatorFromTexture)
	bpy.types.TOPBAR_MT_file_import.append(menu_draw)

def unregister():

	"""This method unregisters the AutomatOperatorFromTexture
operator and the AdjustableOperatorFromTexture operator.  """

	bpy.types.TOPBAR_MT_file_import.remove(menu_draw)
	bpy.utils.unregister_class(AutoOp.AutomatOperatorFromTexture)
	bpy.utils.unregister_class(AdjOp.AdjustableOperatorFromTexture)

# Run register if the file is ran from blenders text editor

if __name__ == "__main__":
	register()
