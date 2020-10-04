import bpy

class GP_OT_install_brush_pack(bpy.types.Operator):
    bl_idname = "gp.import_brush_pack"
    bl_label = "Import texture brush pack"
    bl_description = "import Grease Pencil brush pack from Grease Pencil addon"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        from pathlib import Path

        blendname = 'Official_GP_brush_pack_V1.blend'        
        blend_fp = Path(__file__).parent / blendname
        print('blend_fp: ', blend_fp)

        cur_brushes = [b.name for b in bpy.data.brushes]
        with bpy.data.libraries.load(str(blend_fp), link=False) as (data_from, data_to):
            # load brushes starting with 'tex' prefix if there are not already there
            data_to.brushes = [b for b in data_from.brushes if b.startswith('tex_') and not b in cur_brushes]
            # Add holdout
            if 'z_holdout' in data_from.brushes:
                data_to.brushes.append('z_holdout')

        brush_count = len(data_to.brushes)
        ## force fake user for the brushes
        for b in data_to.brushes:
            b.use_fake_user = True

        if brush_count:
            self.report({'INFO'}, f'{brush_count} brushes installed')
        else:
            self.report({'WARNING'}, 'Brushes already loaded')
        return {"FINISHED"}


def register():
    bpy.utils.register_class(GP_OT_install_brush_pack)

def unregister():
    bpy.utils.unregister_class(GP_OT_install_brush_pack)