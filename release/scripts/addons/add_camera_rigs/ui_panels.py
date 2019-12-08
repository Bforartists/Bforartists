import bpy
from bpy.types import Panel


class ADD_CAMERA_RIGS_PT_camera_rig_ui(Panel):
    bl_category = 'Create'
    bl_label = "Camera Rig UI"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    _ACTIVE_OBJECT: object = None

    _ACTIVE_RIG_TYPE: str = None

    @classmethod
    def poll(self, context):
        self._ACTIVE_OBJECT = bpy.context.active_object

        if self._ACTIVE_OBJECT != None and "rig_id" in self._ACTIVE_OBJECT:
            rigType = self._ACTIVE_OBJECT["rig_id"]

            if rigType == "Dolly_rig" or rigType == "Crane_rig":
                self._ACTIVE_RIG_TYPE = rigType
                return True

        return False

    def draw(self, context):
        arm = self._ACTIVE_OBJECT.data
        poseBones = self._ACTIVE_OBJECT.pose.bones
        activeCameraName = self._ACTIVE_OBJECT.children[0].name

        cam = bpy.data.cameras[bpy.data.objects[activeCameraName].data.name]

        layout = self.layout.box().column()
        layout.label(text="Clipping:")
        layout.prop(cam, "clip_start", text="Start")
        layout.prop(cam, "clip_end", text="End")
        layout.prop(cam, "type")
        layout.prop(cam.dof, "use_dof")
        if cam.dof.use_dof:
            if cam.dof.focus_object is None:
                layout.operator("add_camera_rigs.add_dof_object", text="Add DOF Empty")
            layout.prop(poseBones["Camera"], '["focus_distance"]', text="Focus Distance")
            layout.prop(poseBones["Camera"], '["f-stop"]', text="F-Stop")

        layout.prop(self._ACTIVE_OBJECT, 'show_in_front', toggle=False, text='Show in front')
        layout.prop(cam, "show_limits")
        layout.prop(cam, "show_passepartout")
        if cam.show_passepartout:
            layout.prop(cam, "passepartout_alpha")

        layout.row().separator()
        # added the comp guides here
        layout.operator(
            "wm.call_menu", text="Composition Guides").name = "ADD_CAMERA_RIGS_MT_composition_guides_menu"
        layout.row().separator()

        layout.prop(bpy.data.objects[activeCameraName],
                    "hide_select", text="Make Camera Unselectable")

        layout.operator("add_camera_rigs.add_marker_bind",
                        text="Add Marker and Bind")
        if bpy.context.scene.camera.name != activeCameraName:
            layout.operator("add_camera_rigs.set_scene_camera",
                            text="Make Camera Active", icon='CAMERA_DATA')
        # Camera Lens
        layout.label(text="Focal Length:")
        layout.prop(poseBones["Camera"], '["focal_length"]', text="Focal Length (mm)")

        if self._ACTIVE_RIG_TYPE == "Crane_rig":
            layout = layout.box().column()

            # Crane arm stuff
            layout.label(text="Crane Arm:")
            layout.prop(poseBones["Crane_height"], 'scale', index=1, text="Arm Height")
            layout.prop(poseBones["Crane_arm"], 'scale', index=1, text="Arm Length")

        # Track to Constraint
        layout.label(text="Tracking:")
        layout.prop(poseBones["Camera"], '["lock"]', text="Aim Lock", slider=True)


def register():
    bpy.utils.register_class(ADD_CAMERA_RIGS_PT_camera_rig_ui)


def unregister():
    bpy.utils.unregister_class(ADD_CAMERA_RIGS_PT_camera_rig_ui)
