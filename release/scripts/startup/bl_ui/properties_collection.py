# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
from bpy.types import Panel


class CollectionButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "collection"

    @classmethod
    def poll(cls, context):
        return context.collection != context.scene.collection


def lineart_make_line_type_entry(col, line_type, text_disp, expand, search_from):
    col.prop(line_type, "use", text=text_disp)
    if line_type.use and expand:
        col.prop_search(line_type, "layer", search_from,
                        "layers", icon='GREASEPENCIL')
        col.prop_search(line_type, "material", search_from,
                        "materials", icon='SHADING_TEXTURE')


class COLLECTION_PT_collection_flags(CollectionButtonsPanel, Panel):
    bl_label = "Restrictions"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        collection = context.collection
        vl = context.view_layer
        vlc = vl.active_layer_collection

        col = layout.column(align=True)
        col.prop(collection, "hide_select", text="Selectable", toggle=False, invert_checkbox=True)
        col.prop(collection, "hide_render", toggle=False)

        col = layout.column(align=True)
        col.prop(vlc, "holdout", toggle=False)
        col.prop(vlc, "indirect_only", toggle=False)


class COLLECTION_PT_instancing(CollectionButtonsPanel, Panel):
    bl_label = "Instancing"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        collection = context.collection

        row = layout.row()
        row.prop(collection, "instance_offset")


class COLLECTION_PT_lineart_collection(CollectionButtonsPanel, Panel):
    bl_label = "Line Art"
    bl_order = 10

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        collection = context.collection

        row = layout.row()
        row.prop(collection, "lineart_usage")

        layout.prop(collection, "lineart_use_intersection_mask", text="Collection Mask")

        col = layout.column(align=True)
        col.active = collection.lineart_use_intersection_mask
        row = col.row(align=True, heading="Masks")
        for i in range(8):
            row.prop(collection, "lineart_intersection_mask", index=i, text=" ", toggle=True)
            if i == 3:
                row = col.row(align=True)


classes = (
    COLLECTION_PT_collection_flags,
    COLLECTION_PT_instancing,
    COLLECTION_PT_lineart_collection,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
