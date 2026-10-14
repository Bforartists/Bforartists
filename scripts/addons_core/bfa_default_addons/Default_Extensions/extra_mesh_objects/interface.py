import bpy

def draw_transform_props(self, layout):
    if hasattr(self, 'align'):
        layout.prop(self, 'align', expand=False)
    if hasattr(self, 'location'):
        layout.prop(self, 'location', expand=True)
    if hasattr(self, 'rotation'):
        layout.prop(self, 'rotation', expand=True)