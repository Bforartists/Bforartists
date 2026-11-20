"""Dependency-aware native starter shelf activation and dragging.

Host: Bforartists 5.2 (Blender 5.3); AssetShelf's activation and drag RNA
properties were probed on build 0a1ca45552db. No scene data is imported before
the dependency prompt is accepted. Cancelled drags likewise add nothing.
"""
import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty, FloatVectorProperty
from bpy.types import Operator

from boneforge.i18n import T
from . import rig_assets as ra
from . import quick_human as qh


def viewport_override(context):
    """Keep shelf actions in their originating viewport, including popup execution."""
    area = context.area
    if area is not None and area.type == 'VIEW_3D':
        region = next((r for r in area.regions if r.type == 'WINDOW'), None)
        if region:
            return {"area": area, "region": region}
    return qh._find_view3d_context_override(context)


def available(starter):
    if not starter["requires_rigify"]:
        return True
    return starter["op_id"] in {r["op_id"] for r in qh.discover_rigify_metarigs()}


def reference(context, operator):
    if operator.relative_asset_identifier:
        return operator.relative_asset_identifier
    asset = getattr(context, "asset", None)
    return asset.full_path if asset is not None else ""


def capture_target(operator, context):
    active = context.active_object
    mesh = active if active is not None and active.type == 'MESH' else None
    operator.target_mesh_name = mesh.name if mesh else ""
    operator.target_mesh_uid = str(mesh.session_uid) if mesh else ""
    operator.target_captured = True


# The native shelf supplies these exact property names to both operators.
def reference_properties():
    return {
        # Native shelf callbacks write enum integers directly (CUSTOM is 100).
        # Preserve the host values, including any host-specific library types.
        "asset_library_type": EnumProperty(
            items=[(e.identifier, e.name, e.description, e.value) for e in
                   bpy.types.AssetWeakReference.bl_rna.properties['asset_library_type'].enum_items],
            default='ALL', options={'HIDDEN', 'SKIP_SAVE'}),
        "asset_library_identifier": StringProperty(options={'HIDDEN', 'SKIP_SAVE'}),
        "relative_asset_identifier": StringProperty(options={'HIDDEN', 'SKIP_SAVE'}),
        "target_mesh_name": StringProperty(options={'HIDDEN', 'SKIP_SAVE'}),
        "target_mesh_uid": StringProperty(options={'HIDDEN', 'SKIP_SAVE'}),
        "target_captured": BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}),
        "use_drop_location": BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}),
        "drop_location": FloatVectorProperty(size=3, options={'HIDDEN', 'SKIP_SAVE'}),
    }


class BONEFORGE_OT_add_starter_asset(Operator):
    bl_idname = "boneforge.add_starter_asset"
    bl_label = "Add Starter Rig"
    bl_description = "Add this starter rig; if it needs Rigify, offer to enable Rigify first"
    bl_options = {'REGISTER', 'UNDO'}
    __annotations__ = reference_properties()

    fit_to_active_mesh: BoolProperty(name="Fit Rig to Active Mesh", default=True,
                                    description="Scale and position the starter to the selected mesh")
    parent_with_auto_weights: BoolProperty(name="Parent + Auto-Weight Mesh", default=False,
                                         description="Parent the mesh to the starter with automatic weights")
    generate_control_rig: BoolProperty(name="Add IK/FK Controllers", default=False,
                                      description="Generate Rigify controls after fitting a Rigify starter")

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            cls.poll_message_set("Switch to Object Mode to add a starter rig")
            return False
        return True

    def invoke(self, context, event):
        self.relative_asset_identifier = reference(context, self)
        starter = ra.starter_from_reference(self.relative_asset_identifier)
        if starter is None:
            self.report({'ERROR'}, T("Choose a BoneCraft starter rig"))
            return {'CANCELLED'}
        if not self.target_captured:
            capture_target(self, context)
        if starter["requires_rigify"] and not available(starter):
            # Explicitly requested dependency choice; ordinary additions run immediately.
            self._dependency_prompt = True
            return context.window_manager.invoke_props_dialog(
                self, width=360, title=T("Enable Rigify"),
                confirm_text=T("Enable Rigify & Add Rig"))
        return self.execute(context)

    def draw(self, context):
        starter = ra.starter_from_reference(self.relative_asset_identifier)
        if not getattr(self, '_dependency_prompt', False):
            self.layout.prop(self, 'fit_to_active_mesh')
            self.layout.prop(self, 'parent_with_auto_weights')
            if starter is not None and starter['requires_rigify']:
                self.layout.prop(self, 'generate_control_rig')
            return
        self.layout.label(text=T("Selected starter:") + " " + (starter["label"] if starter else ""))
        self.layout.label(text=T("This starter requires Rigify."))
        self.layout.label(text=T("Enable the installed Rigify and add this rig."))
        self.layout.label(text=T("Nothing is added if you cancel."))

    def execute(self, context):
        self._dependency_prompt = False
        starter = ra.starter_from_reference(self.relative_asset_identifier)
        if starter is None:
            self.report({'ERROR'}, T("Choose a BoneCraft starter rig"))
            return {'CANCELLED'}
        if starter["requires_rigify"] and not available(starter):
            if not qh.enable_rigify_if_available():
                self.report({'ERROR'}, T("Could not enable Rigify. Install or enable it in Preferences > Add-ons, then choose this starter again."))
                return {'CANCELLED'}
            if not available(starter):
                self.report({'ERROR'}, T("This starter is not provided by your installed Rigify version. No rig was added."))
                return {'CANCELLED'}
        override = viewport_override(context)
        if override is None:
            self.report({'ERROR'}, T("Open a 3D Viewport to add this starter rig"))
            return {'CANCELLED'}
        if not self.target_captured:
            capture_target(self, context)
        mesh = context.view_layer.objects.get(self.target_mesh_name) if self.target_mesh_name else None
        if self.target_mesh_name and (mesh is None or mesh.type != 'MESH'
                                     or str(mesh.session_uid) != self.target_mesh_uid):
            self.report({'ERROR'}, T("The chosen mesh is no longer in this view layer"))
            return {'CANCELLED'}
        with context.temp_override(**override):
            # The popup never substitutes a different target for the user's original mesh.
            if mesh is not None:
                for ob in context.selected_objects:
                    ob.select_set(False)
                mesh.select_set(True)
                context.view_layer.objects.active = mesh
            else:
                context.view_layer.objects.active = None
            result = bpy.ops.boneforge.add_quick_rig(
                'EXEC_DEFAULT', rig_op_id=starter["op_id"], rig_label=starter["label"],
                fit_to_active_mesh=self.fit_to_active_mesh,
                parent_with_auto_weights=self.parent_with_auto_weights,
                generate_control_rig=self.generate_control_rig and starter["requires_rigify"])
            if result != {'FINISHED'}:
                return result
            rig = context.active_object
            if mesh is None and rig is not None:
                if self.use_drop_location:
                    rig.location = self.drop_location
                if not self.generate_control_rig or not starter["requires_rigify"]:
                    rig[qh.DROPPED_RIG_PROP] = starter["rig_name"]
                    self.report({'INFO'}, T("Starter added. Choose a mesh in Quick Rig, then use Fit Dropped Rig."))
        return {'FINISHED'}


class BONEFORGE_OT_drag_starter_asset(Operator):
    bl_idname = "boneforge.drag_starter_asset"
    bl_label = "Drag Starter Rig"
    bl_description = "Drop this starter in the viewport; check Rigify before adding any rig"
    __annotations__ = reference_properties()

    @classmethod
    def poll(cls, context):
        return BONEFORGE_OT_add_starter_asset.poll(context)

    def invoke(self, context, event):
        self.relative_asset_identifier = reference(context, self)
        if ra.starter_from_reference(self.relative_asset_identifier) is None:
            self.report({'ERROR'}, T("Choose a BoneCraft starter rig"))
            return {'CANCELLED'}
        capture_target(self, context)
        self._area = context.area
        if self._area is None or self._area.type != 'VIEW_3D':
            return {'CANCELLED'}
        context.window_manager.modal_handler_add(self)
        self._area.header_text_set(T("Drop in the viewport to add the starter; Esc cancels"))
        return {'RUNNING_MODAL'}

    def _clear(self):
        try:
            self._area.header_text_set(None)
        except ReferenceError:
            pass

    def cancel(self, context):
        self._clear()

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self._clear()
            return {'CANCELLED'}
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self._clear()
            region = next((r for r in self._area.regions if r.type == 'WINDOW'), None)
            if region is None or not (region.x <= event.mouse_x < region.x + region.width
                                      and region.y <= event.mouse_y < region.y + region.height):
                return {'CANCELLED'}
            from bpy_extras.view3d_utils import region_2d_to_location_3d
            point = region_2d_to_location_3d(
                region, self._area.spaces.active.region_3d,
                (event.mouse_x - region.x, event.mouse_y - region.y), context.scene.cursor.location)
            with context.temp_override(area=self._area, region=region):
                result = bpy.ops.boneforge.add_starter_asset(
                    'INVOKE_DEFAULT', asset_library_type=self.asset_library_type,
                    asset_library_identifier=self.asset_library_identifier,
                    relative_asset_identifier=self.relative_asset_identifier,
                    target_mesh_name=self.target_mesh_name, target_mesh_uid=self.target_mesh_uid,
                    target_captured=True, use_drop_location=True, drop_location=point)
            return {'CANCELLED'} if result == {'CANCELLED'} else {'FINISHED'}
        return {'RUNNING_MODAL'}


class BONEFORGE_OT_starter_catalog(Operator):
    bl_idname = "boneforge.starter_catalog"
    bl_label = "Starter Rig Catalog"
    bl_description = "Browse all BoneCraft starter rigs by thumbnail and category"

    @classmethod
    def poll(cls, context):
        return BONEFORGE_OT_add_starter_asset.poll(context)

    def execute(self, context):
        return bpy.ops.wm.call_asset_shelf_popover('INVOKE_DEFAULT', name=ra.SHELF_IDNAME)


def draw_add_menu(self, context):
    self.layout.operator_context = 'INVOKE_REGION_WIN'
    self.layout.operator('boneforge.starter_catalog', text=T("Starter Rig Catalog"), icon='OUTLINER_OB_ARMATURE')


_CLASSES = (BONEFORGE_OT_add_starter_asset, BONEFORGE_OT_drag_starter_asset,
            BONEFORGE_OT_starter_catalog)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_armature_add.append(draw_add_menu)


def unregister():
    bpy.types.VIEW3D_MT_armature_add.remove(draw_add_menu)
    for cls in reversed(_CLASSES):
        live = getattr(bpy.types, cls.__name__, None)
        if live is not None:
            bpy.utils.unregister_class(live)
