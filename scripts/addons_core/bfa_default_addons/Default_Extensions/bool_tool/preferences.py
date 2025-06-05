import bpy
from .ui import update_sidebar_category


#### ------------------------------ PREFERENCES ------------------------------ ####

class BoolToolPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    # UI
    show_in_sidebar: bpy.props.BoolProperty(
        name = "Show Addon Panel in Sidebar",
        description = "Add add-on operators and properties to 3D viewport sidebar category.\n"
                    "Most of the features are already available in 3D viewport's Object > Boolean menu, but brush list is only in sidebar panel",
        default = True,
    )
    sidebar_category: bpy.props.StringProperty(
        name = "Category Name",
        description = "Set sidebar category name. You can type in name of the existing category and panel will be added there, instead of creating new category",
        default = "Edit",
        update = update_sidebar_category,
    )

    # Defaults
    solver: bpy.props.EnumProperty(
        name = "Boolean Solver",
        description = "Which solver to use for automatic and brush booleans",
        items = [('FAST', "Fast", ""),
                 ('EXACT', "Exact", "")],
        default = 'FAST',
    )
    wireframe: bpy.props.BoolProperty(
        name = "Display Cutters as Wireframe",
        description = "When enabled cutters will be displayed as wireframes, instead of bounding boxes.\n"
                    "It's better for visualizating the shape, but might be harder to see and have performance cost",
        default = False,
    )
    show_in_editmode: bpy.props.BoolProperty(
        name = "Enable 'Show in Edit Mode' by Default",
        description = "Every new boolean modifier created with brush boolean wil have 'Show in Edit Mode' enabled by default",
        default = True,
    )

    # Advanced
    use_collection: bpy.props.BoolProperty(
        name = "Put Cutters in Collection",
        description = ("Brush boolean operators will put all cutters in same collection, and create one if it doesn't exist.\n"
                       "Useful for scene management, and quickly selecting and removing all clutter when needed"),
        default = True,
    )
    collection_name: bpy.props.StringProperty(
        name = "Collection Name",
        default = "boolean_cutters",
    )
    parent: bpy.props.BoolProperty(
        name = "Parent Cutters to Object",
        description = ("Cutters will be parented to first canvas they're applied to. Works best when one cutter is used one canvas.\n"
                       "NOTE: This doesn't affect Carver tool, which has its own property for this"),
        default = True,
    )
    apply_order: bpy.props.EnumProperty(
        name = "When Applying Cutters...",
        description = ("What happens when boolean cutters are applied on object.\n"
                       "Either when performing auto-boolean, using 'Apply All Cutters' operator.\n"
                       "NOTE: This doesn't apply to Carver tool on 'Destructive' mode; or when applying individual cutters"),
        items = (('ALL', "Apply All Modifiers", "All modifiers on object will be applied (this includes shape keys as well)"),
                 ('BEFORE', "Apply Booleans & Everything Before", "Alongside boolean modifiers all modifiers will be applied that come before the last boolean"),
                 ('BOOLEANS', "Only Apply Booleans", "Only apply boolean modifiers. This method will fail if object has shape keys")),
        default = 'ALL',
    )
    pin: bpy.props.BoolProperty(
        name = "Pin Boolean Modifiers",
        description = ("When enabled boolean modifiers will be placed above every other modifier on the object (if there are any).\n"
                       "Order of modifiers can drastically affect the result (especially when performing auto boolean).\n"
                       "NOTE: This doesn't affect Carver tool, which has its own property for this"),
        default = False,
    )

    # Features
    double_click: bpy.props.BoolProperty(
        name = "Double-click Select",
        description = ("Select boolean cutters by dbl-clicking on the boolean modifier.\n"
                       "This feature works in entire modifier properties area, not just on boolean modifier header,\n"
                       "therefore can result in lot of misclicks and unintended selections."),
        default = False,
    )

    # Debug
    versioning: bpy.props.BoolProperty(
        name = "Versioning",
        description = "Because of the drastic changes in add-on data, it's necessary to do versioning when loading old files\n"
                    "where Bool Tool cutters(brushes) are not applied. If you don't have files like that, you can ignore this"
    )
    experimental: bpy.props.BoolProperty(
        name = "Experimental",
        description = "Enable experimental features",
        default = False,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # UI
        col = layout.column(align=True, heading="Show in Sidebar")
        row = col.row(align=True)
        sub = row.row(align=True)
        sub.prop(self, "show_in_sidebar", text="")
        sub = sub.row(align=True)
        sub.active = self.show_in_sidebar
        sub.prop(self, "sidebar_category", text="")

        # Defaults
        layout.separator()
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "solver", text="Solver", expand=True)
        col.prop(self, "wireframe")
        col.prop(self, "show_in_editmode")

        # Advanced
        layout.separator()
        col = layout.column(align=True, heading="Put Cutters in Collection")
        row = col.row(align=True)
        sub = row.row(align=True)
        sub.prop(self, "use_collection", text="")
        sub = sub.row(align=True)
        sub.active = self.show_in_sidebar
        sub.prop(self, "collection_name", text="")

        # col = layout.column(align=True, heading="Advanced")
        col.prop(self, "parent")
        col.prop(self, "apply_order")
        col.prop(self, "pin")

        # Features
        layout.separator()
        col = layout.column(align=True, heading="Features")
        col.prop(self, "double_click")

        # Experimentals
        layout.separator()
        col = layout.column(align=True)
        col.prop(self, "versioning", text="⚠ Versioning")
        col.prop(self, "experimental", text="⚠ Experimental")



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    BoolToolPreferences,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
