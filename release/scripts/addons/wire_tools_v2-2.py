######################################################################################################
# Add some options in 3D View > Properties > Shading to display wire for all objects                 #
# Actualy partly uncommented - if you do not understand some parts of the code,                      #
# please see further version or contact me.                                                          #
# Author: Lapineige                                                                                  #
# License: GPL v3                                                                                    #
######################################################################################################

bl_info = {
    "name": "Wire Tools",
    "description": 'Quickly enable wire (into solid mode) to all objects, with some more shading tool',
    "author": "Lapineige",
    "version": (2, 2),
    "blender": (2, 75, 0),
    "location": "3D View > Properties Panel > Shading",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "http://blenderlounge.fr/forum/viewtopic.php?f=18&t=736",
    "category": "3D View"}

import bpy
   
class WT_HideAllWire(bpy.types.Operator):
    """Hide object's wire and edges"""
    bl_idname = "object.wt_hide_all_wire"
    bl_label = "Hide Wire And Edges"

    @classmethod
    def poll(cls, context):
        return not bpy.context.scene.WT_handler_enable

    def execute(self, context):
        for obj in bpy.data.objects:
            if (not context.scene.WT_only_selection)  or  (obj.select and context.scene.WT_only_selection and not context.scene.WT_invert)  or  ((context.scene.WT_invert and context.scene.WT_only_selection) and not obj.select):
                if hasattr(obj,"show_wire"):
                    obj.show_wire,obj.show_all_edges = False,False
        return {'FINISHED'}

class WT_DrawOnlyBounds(bpy.types.Operator):
    """Display only object boundaries"""
    bl_idname = "object.wt_draw_only_box"
    bl_label = "Draw Only Bounds"

    @classmethod
    def poll(cls, context):
        return not bpy.context.scene.WT_handler_enable

    def execute(self, context):
        for obj in bpy.data.objects:
            if (not context.scene.WT_only_selection)  or  (obj.select and context.scene.WT_only_selection and not context.scene.WT_invert)  or  ((context.scene.WT_invert and context.scene.WT_only_selection) and not obj.select):
                if hasattr(obj,"draw_type"):
                    obj.draw_type = 'BOUNDS'
                    obj.show_wire = False
                    obj.show_all_edges = False
        return {'FINISHED'}
    
class WT_DrawTextured(bpy.types.Operator):
    """Display object in textured mode"""
    bl_idname = "object.wt_draw_textured"
    bl_label = "Draw Textured"

    @classmethod
    def poll(cls, context):
        return not bpy.context.scene.WT_handler_enable

    def execute(self, context):
        for obj in bpy.data.objects:
            if (not context.scene.WT_only_selection)  or  (obj.select and context.scene.WT_only_selection and not context.scene.WT_invert)  or  ((context.scene.WT_invert and context.scene.WT_only_selection) and not obj.select):
                if hasattr(obj,"draw_type"):
                    obj.draw_type = 'TEXTURED'                   
        return {'FINISHED'}

class WT_DrawWireEdges(bpy.types.Operator):
    """Display the object's wire (all edges)"""
    bl_idname = "object.wt_draw_wire_and_edges"
    bl_label = "Draw Wires and Edges"

    @classmethod
    def poll(cls, context):
        return not bpy.context.scene.WT_handler_enable

    def execute(self, context):
        for obj in bpy.data.objects:
            if (not context.scene.WT_only_selection)  or  (obj.select and context.scene.WT_only_selection and not context.scene.WT_invert)  or  ((context.scene.WT_invert and context.scene.WT_only_selection) and not obj.select):
                if hasattr(obj,"show_wire"):
                    obj.show_wire,obj.show_all_edges = True,True
                    obj.draw_type = 'TEXTURED' # to prevent from a "bug" displaying bounds and wire
        return {'FINISHED'}
    
class WT_DrawOnlyWire(bpy.types.Operator):
    """Display the object's wire"""
    bl_idname = "object.wt_draw_only_wire"
    bl_label = "Draw Only Wire"

    @classmethod
    def poll(cls, context):
        return not bpy.context.scene.WT_handler_enable

    def execute(self, context):
        for obj in bpy.data.objects:
            if (not context.scene.WT_only_selection)  or  (obj.select and context.scene.WT_only_selection and not context.scene.WT_invert)  or  ((context.scene.WT_invert and context.scene.WT_only_selection) and not obj.select):
                if hasattr(obj,"show_wire"):
                    obj.show_wire,obj.show_all_edges = True,False
                    obj.draw_type = 'TEXTURED' # to prevent from a "bug" displaying bounds and wire
        return {'FINISHED'}

class WT_SelectionHandlerToggle(bpy.types.Operator):
    """ Display the wire of the selection, auto update when selecting another object"""
    bl_idname = "object.wt_selection_handler_toggle"
    bl_label = "Wire Selection (auto)"
    bl_options= {'INTERNAL'}
    
    def execute(self, context):
        if context.scene.WT_handler_enable:
            try:
                bpy.app.handlers.scene_update_post.remove(wire_on_selection_handler)
            except:
                print('WireTools: auto mode exit seams to have failed. If True, reload the file')
            context.scene.WT_handler_enable = False
            if hasattr(context.object,"show_wire"):
                        context.object.show_wire , context.object.show_all_edges = False,False
        else:
            bpy.app.handlers.scene_update_post.append(wire_on_selection_handler)
            context.scene.WT_handler_enable = True
            if hasattr(context.object,"show_wire"):
                            context.object.show_wire , context.object.show_all_edges = True,True
        return {'FINISHED'}

def shading_wire_tools_layout(self,context):
    layout = self.layout
    
    
    if not context.scene.WT_display_tools:
        layout.prop(context.scene,"WT_display_tools", emboss=False, icon="TRIA_RIGHT", text="Wire Tools")
    else:
        layout.prop(context.scene,"WT_display_tools", emboss=False, icon="TRIA_DOWN", text="Wire Tools")
        
        if context.scene.WT_handler_enable:
            layout.operator('object.wt_selection_handler_toggle', icon='X')
        else:
            layout.operator('object.wt_selection_handler_toggle', icon='MOD_WIREFRAME')
        
        split = layout.split(percentage=.75, align=True)
        split.enabled = not context.scene.WT_handler_enable
        split.prop(context.scene,"WT_only_selection", toggle=True, icon="BORDER_RECT")
        row = split.row(align=True)
        row.enabled = context.scene.WT_only_selection
        row.prop(context.scene,"WT_invert",toggle=True)
        
        
        col = layout.column(align=True)
        col.operator("object.wt_draw_wire_and_edges", icon="WIRE", text="Wire + Edges")
        col.operator("object.wt_draw_only_wire", icon="SOLID", text="Wire")
        col.operator("object.wt_hide_all_wire", icon="RESTRICT_VIEW_ON", text="Hide All")
        col = layout.column(align=True)
        col.operator("object.wt_draw_only_box", icon="BBOX", text="Only Bounds")
        col.operator("object.wt_draw_textured", icon="MATCUBE", text="Textured")

#handler
def wire_on_selection_handler(scene):
    obj = bpy.context.object
    
    if not scene.WT_handler_previous_object:
        if hasattr(obj,"show_wire"):
            obj.show_wire , obj.show_all_edges = True,True
            scene.WT_handler_previous_object = obj.name
    else:
        if scene.WT_handler_previous_object != obj.name:
            previous_obj = bpy.data.objects[scene.WT_handler_previous_object]
            if hasattr(previous_obj,"show_wire"):
                        previous_obj.show_wire , previous_obj.show_all_edges = False,False
                        
            scene.WT_handler_previous_object = obj.name
            
            if hasattr(obj,"show_wire"):
                            obj.show_wire , obj.show_all_edges = True,True

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_PT_view3d_shading.append(shading_wire_tools_layout)
    bpy.types.Scene.WT_handler_enable = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.WT_handler_previous_object = bpy.props.StringProperty(default='')
    bpy.types.Scene.WT_only_selection = bpy.props.BoolProperty(name="Only Selection", default=False)
    bpy.types.Scene.WT_invert = bpy.props.BoolProperty(name="Invert", default=False)
    bpy.types.Scene.WT_display_tools = bpy.props.BoolProperty(name="Display WireTools paramaters", default=False)


def unregister():
    bpy.types.VIEW3D_PT_view3d_shading.remove(shading_wire_tools_layout)
    if bpy.context.scene.WT_handler_enable:
        bpy.app.handlers.scene_update_post.remove(wire_on_selection_handler)
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
