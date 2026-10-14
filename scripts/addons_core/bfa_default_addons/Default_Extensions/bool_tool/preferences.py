import bpy
from . import ui


#### ------------------------------ FUNCTIONS ------------------------------ ####

def update_sidebar_category(self, context):
    """Change sidebar category of add-ons panel."""

    panel_classes = [
        ui.panels.VIEW3D_PT_boolean,
        ui.panels.VIEW3D_PT_boolean_helpers,
        ui.panels.VIEW3D_PT_boolean_cutters,
    ]

    for cls in panel_classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
        cls.bl_category = self.sidebar_category
        bpy.utils.register_class(cls)



#### ------------------------------ PREFERENCES ------------------------------ ####

class BoolToolPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    # UI
    category: bpy.props.EnumProperty(
        name = "Category",
        items = (('ADDON', "Add-on", "General add-on features"),
                 ('SHARED', "Shared", "Features shared by all of add-ons operators and tools"),
                 ('OPERATORS', "Boolean Operators", "Features for brush and auto Boolean operators")),
        default = 'OPERATORS'
    )

    show_in_sidebar: bpy.props.BoolProperty(
        name = "Show Add-on Panel in Sidebar",
        description = "Add a sidebar panel in 3D Viewport with add-ons operators and properties",
        default = True,
    )
    sidebar_category: bpy.props.StringProperty(
        name = "Category Name",
        description = "Sidebar category name. Using the name of the existing category will add the panel there",
        default = "Edit",
        update = update_sidebar_category,
    )

    # Defaults
    solver: bpy.props.EnumProperty(
        name = "Boolean Solver",
        description = "Which solver to use for automatic and brush Boolean operators",
        items = [('FLOAT', "Float", ""),
                 ('EXACT', "Exact", ""),
                 ('MANIFOLD', "Manifold", "")],
        default = 'FLOAT',
    )
    display: bpy.props.EnumProperty(
        name = "Cutter Display",
        items = (('WIRE', "Wire", "Display the cutter object as a wireframe"),
                 ('BOUNDS', "Bounds", "Display only the bounds of the cutter object")),
        default = 'BOUNDS'
    )
    show_in_editmode: bpy.props.BoolProperty(
        name = "Enable 'Show in Edit Mode' by Default",
        description = "Added Boolean modifiers will have 'Show in Edit Mode' enabled by default",
        default = True,
    )

    # Advanced
    use_collection: bpy.props.BoolProperty(
        name = "Put Cutters in Collection",
        description = ("Put all cutters in the same collection, and create one if it doesn't exist"),
        default = True,
    )
    collection_name: bpy.props.StringProperty(
        name = "Collection Name",
        description = "Name of the collection where cutters will be added",
        default = "boolean_cutters",
    )
    parent: bpy.props.BoolProperty(
        name = "Parent Cutters to Object",
        description = ("Cutters will be parented to first canvas they're applied to"),
        default = True,
    )
    apply_order: bpy.props.EnumProperty(
        name = "Apply Modifiers",
        description = ("Which modifiers to apply when using add-ons destructive operators.\n"
                       "NOTE: This option is not used when applying individual cutters"),
        items = (('ALL', "All",
                  "All modifiers on object (and shape keys) will be applied during destructive operators"),
                 ('BEFORE', "Booleans & Everything Before",
                  "Apply all modifiers that come before the last Boolean modifier in the stack"),
                 ('BOOLEANS', "Booleans",
                  "Only apply Boolean modifiers")),
        default = 'ALL',
    )
    pin: bpy.props.BoolProperty(
        name = "Pin Boolean Modifiers",
        description = ("Always make new Boolean modifiers first in the modifier stack.\n"
                       "NOTE: Order of modifiers can drastically affect the final result"),
        default = False,
    )

    # Features
    fast_modifier_apply: bpy.props.BoolProperty(
        name = "Faster Destructive Booleans",
        description = ("Experimental method of applying modifiers that results in 30-50% faster destructive Booleans.\n"
                       "However, changing modifier properties in the redo panel (like material transfer)\n"
                       "is not available for this method yet."),
        default = False,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # UI
        row = layout.row()
        row.prop(self, "category", expand=True)
        layout.separator()

        # Add-on Properties
        if self.category == 'ADDON':
            col = layout.column(align=True, heading="Show in Sidebar")
            row = col.row(align=True)
            sub = row.row(align=True)
            sub.prop(self, "show_in_sidebar", text="")
            sub = sub.row(align=True)
            sub.active = self.show_in_sidebar
            sub.prop(self, "sidebar_category", text="")

            col.separator()
            col = layout.column(align=True, heading="Features")
            col.prop(self, "fast_modifier_apply")

        # Shared Properties
        if self.category == 'SHARED':
            col = layout.column()
            col.prop(self, "show_in_editmode")
            col.prop(self, "apply_order")

        # Boolean Operator Properties
        if self.category == 'OPERATORS':
            col = layout.column(align=True, heading="Put Cutters in Collection")
            row = col.row(align=True)
            sub = row.row(align=True)
            sub.prop(self, "use_collection", text="")
            sub = sub.row(align=True)
            sub.active = self.show_in_sidebar
            sub.prop(self, "collection_name", text="", placeholder="boolean_cutters")

            col = layout.column()
            row = col.row(align=True)
            row.prop(self, "solver", text="Solver", expand=True)
            row = col.row(align=True)
            row.prop(self, "display", expand=True)

            col = layout.column()
            col.prop(self, "parent")
            col.prop(self, "pin")



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = (
    BoolToolPreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
